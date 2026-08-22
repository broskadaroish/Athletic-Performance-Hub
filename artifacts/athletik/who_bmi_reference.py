"""Lokale WHO BMI-for-age-Referenz (Growth Reference 2007).

Quelle (offizielle WHO-Downloads, abgerufen am 22.08.2026):
https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age

Verwendet wurden die erweiterten Tabellen:
- bmi-girls-z-who-2007-exp.xlsx (SHA-256:
  66f5c6284b44579ad6135fc639f22c09e36fe5a695b04390377113f6a00deb72)
- bmi-boys-z-who-2007-exp.xlsx (SHA-256:
  0a60849673f34a06b8e2fe4defe5d00348de687b6c9fce0278f1525fff89eb6d)

Der komprimierte Payload enthält je Geschlecht die vier offiziellen BMI-Grenzen
(-3 SD, -2 SD, +1 SD, +2 SD) für jeden vollen Monat 61 bis 228. Die Daten
werden ohne Netzwerkzugriff geladen. Zwischen zwei Monatswerten werden nur die
offiziellen Grenzwerte linear interpoliert; es werden keine Grenzwerte ergänzt.
"""

from __future__ import annotations

import base64
import json
import math
import zlib
from functools import lru_cache


_FIRST_MONTH = 61
_LAST_MONTH = 228

# zlib + Base85 von {"female": [[-3SD, -2SD, +1SD, +2SD], ...], "male": [...]}
# Die Daten sind absichtlich im Quellcode versioniert, damit die Laufzeit keine
# externe medizinische Referenz nachladen muss.
_REFERENCE_B85 = (
    "c-mc>O_HUl4Mq3T<BAMGKL~HdQ3DU`k-Y+k_ipK4=~ZQoI<ik8Bmn~5@BR0$fBo}6|M>Sm|N7hC|GxLvy+8K(x*9*We?|TgUt#g{"
    "2bc@tCVZgbO^riEK?C${8+t$w43p`MR3{U#y+Q9C%8{ER>mR+ZwO&)<tQ)gFaZo)&=`kFB2KKQ_v>eQ};NCOv(Cng16>3tQL>wcf"
    "T^imop&nZPvG3QaVBXg`It;=1d!Pq)kALVU4N$#BW!WE;W1Up*H_Mzg$lm_$QTcnn_KKn^{zo(lD)3n2&rHDbHss09C;giVre)^I"
    "?&L{md3({bFxJmd<*H-o;k5o?_Sr584R&*D&1T}PWj<+;#`t8xZ7M}&gN9BPotv%pV^S>LThg$7a>Bq~dp<On#tW+Z{x~bwaOfiq"
    "Osi?X=xmBuqz^7@MA5D7a%{{S3*p-FqGxxwao}<s%xk$-i$*VQ2*M3Pl6`^7$1+nD4A(QQNp*Lc!;$82%<F-ObP|aZo;0vA^1LK8"
    "pJ^Y4z6HaTxTHQS^f2oK3uNNXiGAEq4@Scg>WvwvNW?Sj@wZ_$y!YaB>~S8C`Xk|+k@-I*>jH|$+R1kQXXb2L=OC$rB9N2+h^%&8"
    "WCakg7+UouX=NyBxx4egN>d}PKqD9I6&2RCq!*U=hUIfHtMce1t#h1I3(A3E+if`gFXk92u>oI?+*N>+qKaxdn9!NQgjJ*^eR0r-"
    "a9HzB)hIxPzh<x-*7Pj+dmM&6|2kNarh-||gJG{sRC+p3rwW5)9LR8$lv7bOWFo{c?G3=3jZ_wb6=XORcF!AlkYVMWkVPn=#6ZJH"
    "72YT5cT&BbCgH5CqDxM}2~`)|wS}s)9wzl!Rz(U;aQwILg4e8}!K}HlvSVmyPpZtYJ=EA!>94)shHYb7XR*r@dvfzgM`Ma;DzjC9"
    "^KMAGrPFU06v1d(Pj)8x&J14Oe&(QZ+O7*}8ORDNu&bvxsdK*sJi2vm()-h~`a?9q9Ae?p!P72Xu1y3o5eCC|#$GS@4l8WtGGTn+"
    "!>o_BEN}CoSs6&93~T;x(#Sk%U6xIAL5i}L)qYR9Cl^usQ*i}WmCTKk^h_3?VC=5sW|cezWftH$rrr5ms4`eg`I4x@BE=3XQa+Co"
    "8V`Ea4ls+ZkOkd#!wajm%d0{v=DgNJ_r_RJ*1>~W!+Y#DxSJO_>fk~m(#@uI@o8P;p!wIaoUT1SOri$HzN$W!vGv$f+gEwjWT7-G"
    "dZNb)qcxVSokugNM2{7PSH4jo&Vglp?Xz5XRr{)n;eus*9j{ik)w&Hp1D2hYEvaGgZn=}CvKGQJ?Dk3@a)ntf>rJx9$59<t_=NJ2"
    ")v$`9=c2X8=I|*V3f`?c?fDLB>I<{h<FU$NvGZYyOgxt0sJqNFsG%85ru@KNTu7d!rCqxDKq!iuwG=Q5PD7J|xNfRYlCtV04H({b"
    "St)l>e?l6$OOm3Xor_p*bbjj;7E{<2LmuLGe&b=*!wRf*DC>1gh>O`!ajR0+3e_{SVI8`JRa+9~lOSQgUy?p}qzlyRAk>o%iKvt7"
    "pbA<~#-ws~Q$wtH5*@sgk}Bt|bBuVb%k0Ix{X)s3x=E{ypv)F!jo0$7pjY;UPl9~ov`=`dCKS}lbrI}6J@hQ3!fU#^qOE8wZCbBJ"
    ";~uV?7Vx%9r`{-r*Jr^Cm!5U7hYNczO25>Oi+MukIp0WQ(6Btx*JDL6HWcyHQAxV3=M~Ny7ql*#q}_KU4Y>T6i`o@Y?`FbUwt~Xy"
    "ZUtxU>KZC$$dgx|@>Q|hC8br~3s~5MK4$CCITK%7`V{S}MX}yR>!jw!6w)BH%D?lWRu@dMep^<}La(<tYwg;iF_hhDH918u?B35<"
    "gW-)kV{Ht*ta>bW1q}s!A-{3Pr9h*&FY5PRh&67n9NELbdY+w6>sxgaP2?d&EYEs-SGJ2CTqvjM8!E7SYX2#oSf^ex9g8bsIlOP`"
    "Myu|&nQ>&^J$1t!jNEHHa#H#$wUb^|`KA~7MdenO=%iyfkR#b}xT<-=v-VIdxya__Njf=th*cEH*Na)toYrop#c%^!m4T!oLlLVu"
    "d@?{;?J&B}gqN@`kEAj~H-eR*VYnn_1L^RCPtIB8cK*>*S4HQIe&DgZnU-s(by{mRumIg!=_noO5-X>GGKR4ul()UtG9>)?BnU^D"
    "L_Eoo-ZPYA1$J@f-mik#>WebR7n!hSe?Y9=bvSGvyNrhUzg%_u<#1EP8jFVQJLF3&4w7iD-)D8q8rX?;?{|1PlsnOWMZ;LRi{rwu"
    "uaC!E9oh{<<6FNck*ogbu%FMuK2nT*$Z)<HzONil#}f|K@##1z4IA?B_MwdDUB1*f_Wu0&<FAj%me+l^ob=Jzc^;egZX27`OB(DR"
    "r!!;=u{e<%`mOW+fQJx$kxZlYp`6w)JJ0xITGER)Pi)}*9R}f@p7ZQad+ijcl78CN(}t0_+RxRP&Rf5p;>ZQyflq4PoNVDxZZIf1"
    "N#lO&gBLP!9WA1rVcpdui8t8qj=x5;#!2aK@48P1y__;9-1TXfsyP6}1`0OP?vo}?dNFA@TKl_Z)?lQ(NFw0V)fw6n1&id{?4zgC"
    "?bbXiIAu=u%Ae+Y{}LKn%dESpU9QWeDD(dwTj?{sxlo3ne6;qo($m&cqxfBrTzm8arw&1}W?gEpKGU*cMZ!vSbPB9P14-Ug%QidL"
    "?GrBh&P}y!Q|cU#WnnKKie>vzL!G?{y|22T-(|(mCYKg51nSeF>MPM_OW61yh1Pi<o9!`dPIUy*V5_9BQ&I2Yf){p$Exe6nPy$ZT"
    "fX7PF!S~Qd>4ZvJ751Wc<OW778$MN`gc90mq+|eZ^5M%Kexwr>+EsXL3Pqx|w4_SA&Y=O1-)wW`(#oZ%c#x+#(0Z{tLU|93UUuno"
    "W|iAqxjdI`?>?h|ETp)uzM@L{MjoMJLl&@mY~&Hj7-$hMdLVT0cf=FwL|1;36=jykoMRt?eG84c&TcabMMjSwmD{Nm#?>*d`+G3#"
    "qth`>#tKfk!lyjddjY*Cjw4izRo_sWw#XDX=vy#p$QxA#hU-C6^g^z9b9m|*zJ<#YX!MId9nl7<m}}*-!=Lkk=aBrW{-ArJy)3xS"
    "uQ$T6ANAz2ZhlHQI&qnDaJemDB5*Bd3qNuXCcV6nY9))!u?t=<H<WdlQs}G>^lhOwo~2gN-`fm@-4KlQhmm)ZSlxP2TvoTm&e`Gh"
    "B!GAY8ZCD2(TP|yy9}31UOoKkv-7AszE&j<dhOM-z81cyqP{?zzGGx0tm~sZ2vMLa<w!+`+SNe`*b7vABq)kO%eq!#R<-j@X6jEr"
    "=b$4t7O%QEAY<SfuV*z{{C@FN@dspu5QU6-&l?Sjsu({SQLl(|MuIZRV$c@xP&?E4RBKGpOrZgmzFEEYYQu*z62#$p)}ayHt39TA"
    "B{V#Z_~=AJ&5Wuf`{6U{h!6$_2HQZ18HfZc(-0R^YP7p0v!SWwXCFn6ZqbXQ^{7gUqqsJu(2>*X*^JgSK8j^2t{sa8f-zPls5(-e"
    "dW%!A>kD$`q3qiiut4WRug7w?4qMaFwE}9I2Pqq%?H!NP<I7U1inn`zyAY@}Md_5W7x`>9e@J62)E0XfJ9;Oc&-Io^E`0i~b{SvT"
    "N^IkIA8R?ZPe80gu?^wId2CcVpb%JoUGOM)#)zf0V9?ueGrWG=TW9%gs1fyHv<jX>mR#21z7gCgX+k~Rb9nG5YQ1gqJ5Fh6Z}cl_"
    "Y70ZpqZ+E+E-Z?G^=PPSSS7QxuI@uNm88S(FiM@(22wvMVW%pdz$qW;We3zCG_D&eLeeXvBpv8I_)M_bL)z%;%BPv(rpD(VXr<Gd"
    "p4XZhE22X2T>B$4U21A5rmrrDl2b;ax^UU|W<^xc*8wR7ET?X{0=nfHX+~{RH)BaO%qt_ID3!je)I4i{RM$A#3^m02Ft2P_wpk%_"
    "EN*=R#rGkoo}WZwB;`e=Mmx<k1eVN9S4*nKADz!HQv9fSI_He|2o@Bum<bQ~`$qh_N|DNxACI7ju8{%nr8M>sYfus0orvIX88$Ud"
    ">Y*c+27j2bd8@n&Ve&*TY*3s*@vq*;A+(O<`6z^x@?W)dgQ~XW7H1YJ*A74%3G21$qo`cRFfGr!p%y}5x%}(|iPpJrHXWEA(uYu6"
    "k28KEtz~v<nvX)Ok?w^w*|PpBMWuBp(qt4`jfVS6TYcyN4BQP)t+cnev1iB)vipk_^t#1gEg1VH=OE!nuY7`y;X?({AEim9luF%="
    "$~yX3s*f<-*SqmDbNr0vmozDp3X#Wd6q>}MAS$neE#<4aMxk<9<>b>R8*i@aI3YW1qnNsTtTGua{~JEp?QoQG>7(8H^b4uAp?5<`"
    "C2*A1j#Vl4J!&2GV~G+|wb$MD;ZIyB6bcOA*JF(h*rJ{UF{OTJ)R0g7lK%0P4MY1k8dlm7`aUX<knCbE0po|)`Z7V;je^pe4OO44"
    "@H-XUD|Ld4&e-~D)W1`KK1R*7r*%4YsLI8L?lT#7_I>yQh|hO`6RfjQI(=Vp=$Q>wpAqmo6<%hKx@QlC##rqp?u|u<MS4Twmsl6y"
    "k&WN*-qcg8PmJ>;mb&T|WyJCLvMsOfvZ&tQBuL{^{PJ?C;{xGLU+=cd9OEZ0x#i_jD(ox<e+vXjuMWhf;Md!t)WM<;0ktsgt4m36"
    "Ti7Obr}WnIh9VipWGIv2(a8uS<%dC~9Gl(F&!7MMKX7CRKL"
)


@lru_cache(maxsize=1)
def _reference_rows() -> dict[str, list[list[float]]]:
    """Dekodiert die lokal versionierte Referenz und prüft ihre Vollständigkeit."""
    try:
        rows = json.loads(zlib.decompress(base64.b85decode(_REFERENCE_B85)).decode("utf-8"))
    except Exception as exc:  # Fail closed: keine medizinische Ersatzlogik.
        raise RuntimeError("WHO-BMI-Referenzdaten sind nicht lesbar.") from exc
    expected = _LAST_MONTH - _FIRST_MONTH + 1
    if set(rows) != {"female", "male"} or any(len(rows[key]) != expected for key in rows):
        raise RuntimeError("WHO-BMI-Referenzdaten sind unvollständig.")
    return rows


def who_bmi_grenzen(geschlecht: str, alter_monate: float) -> tuple[float, float, float, float] | None:
    """Gibt (-3 SD, -2 SD, +1 SD, +2 SD) für 61–228 Monate zurück.

    Die WHO-Tabelle liegt je vollem Monat vor. Für das exakte kalendarische
    Alter zwischen zwei Monaten interpoliert diese Funktion ausschließlich die
    zwei benachbarten WHO-Tabellenzeilen.
    """
    if geschlecht not in {"female", "male"} or not math.isfinite(alter_monate):
        return None
    if not _FIRST_MONTH <= alter_monate <= _LAST_MONTH:
        return None

    position = alter_monate - _FIRST_MONTH
    lower_index = math.floor(position)
    upper_index = min(lower_index + 1, _LAST_MONTH - _FIRST_MONTH)
    fraction = position - lower_index
    rows = _reference_rows()[geschlecht]
    lower, upper = rows[lower_index], rows[upper_index]
    return tuple(
        round(float(lower[index]) + (float(upper[index]) - float(lower[index])) * fraction, 4)
        for index in range(4)
    )