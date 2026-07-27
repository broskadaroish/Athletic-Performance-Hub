# =====================================
# FMS Berechnung
# =====================================


def fms_score_berechnen(

    deep,

    hurdle_l,
    hurdle_r,

    inline_l,
    inline_r,

    shoulder_l,
    shoulder_r,

    aslr_l,
    aslr_r,

    trunk,

    rotary_l,
    rotary_r

):

    score = (

        deep

        + min(hurdle_l, hurdle_r)

        + min(inline_l, inline_r)

        + min(shoulder_l, shoulder_r)

        + min(aslr_l, aslr_r)

        + trunk

        + min(rotary_l, rotary_r)

    )


    return score





# =====================================
# FMS Bewertung
# =====================================

def fms_bewertung(score):


    if score <= 12:

        return "Hohes Risiko"



    elif score <= 17:

        return "Beobachten"



    else:

        return "Geringes Risiko"





# =====================================
# Asymmetrie erkennen
# =====================================

def asymmetrie_pruefen(werte):


    anzahl = 0


    for links, rechts in werte:


        if links != rechts:

            anzahl += 1



    if anzahl == 0:

        return "Keine Asymmetrie"



    elif anzahl == 1:

        return "Eine Asymmetrie"



    else:

        return f"{anzahl} Asymmetrien"





# =====================================
# Trainingsschwerpunkt
# =====================================

def fms_problem_analyse(score, asymmetrie):


    if score <= 12:

        return "FMS Defizite + Stabilitätstraining"



    elif "Asymmetrie" in asymmetrie or "asymmetrie" in asymmetrie:

        return "Asymmetrien korrigieren"



    else:

        return "Kein akuter Handlungsbedarf"