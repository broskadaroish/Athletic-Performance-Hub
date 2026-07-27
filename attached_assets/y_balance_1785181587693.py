# =====================================
# Y-Balance Test Berechnung Fußball
# =====================================


def y_balance_berechnen(

    anterior_r,
    anterior_l,

    posteromedial_r,
    posteromedial_l,

    posterolateral_r,
    posterolateral_l,

    beinlaenge_r,
    beinlaenge_l

):


    # =====================================
    # Differenzen Links / Rechts
    # =====================================


    diff_anterior = abs(
        anterior_r - anterior_l
    )


    diff_posteromedial = abs(
        posteromedial_r - posteromedial_l
    )


    diff_posterolateral = abs(
        posterolateral_r - posterolateral_l
    )



    # =====================================
    # Composite Score Berechnung
    # =====================================


    if beinlaenge_r > 0:


        composite_r = (

            (
                anterior_r
                +
                posteromedial_r
                +
                posterolateral_r
            )
            /
            3

        ) / beinlaenge_r * 100


    else:

        composite_r = 0




    if beinlaenge_l > 0:


        composite_l = (

            (
                anterior_l
                +
                posteromedial_l
                +
                posterolateral_l
            )
            /
            3

        ) / beinlaenge_l * 100


    else:

        composite_l = 0





    # =====================================
    # Asymmetrien erkennen
    # =====================================


    asymmetrien = []



    if diff_anterior >= 4:

        asymmetrien.append(
            "Anterior"
        )



    if diff_posteromedial >= 4:

        asymmetrien.append(
            "Posteromedial"
        )



    if diff_posterolateral >= 4:

        asymmetrien.append(
            "Posterolateral"
        )





    if len(asymmetrien) == 0:


        asymmetrie = (
            "Keine relevante Asymmetrie"
        )


    else:


        asymmetrie = (

            "Asymmetrie: "
            +
            ", ".join(asymmetrien)

        )





    # =====================================
    # Trainingsschwerpunkt Fußball
    # =====================================


    if diff_posteromedial >= 4:


        schwerpunkt = (

            "Hüftstabilität + "
            "Gluteus medius + "
            "Beckenstabilität"

        )



    elif diff_posterolateral >= 4:


        schwerpunkt = (

            "Kniekontrolle + "
            "seitliche Stabilität"

        )



    elif diff_anterior >= 4:


        schwerpunkt = (

            "Sprunggelenk Mobilität + "
            "Knie Vorschub verbessern"

        )



    else:


        schwerpunkt = (

            "Keine Auffälligkeit. "
            "Leistungsorientiertes Training möglich."

        )






    # =====================================
    # Ergebnis zurückgeben
    # =====================================


    return {


        "diff_anterior":
        round(diff_anterior,1),



        "diff_posteromedial":
        round(diff_posteromedial,1),



        "diff_posterolateral":
        round(diff_posterolateral,1),




        "composite_rechts":
        round(composite_r,1),




        "composite_links":
        round(composite_l,1),




        "asymmetrie":
        asymmetrie,




        "schwerpunkt":
        schwerpunkt

    }