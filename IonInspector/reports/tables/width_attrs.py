def width_attrs(width):
    return {"th": {"style": "width: %s" % width}, "td": {"class": "no-underline"}}


width_8_attrs = width_attrs("8vw")
width_15_attrs = width_attrs("15vw")
width_30_attrs = width_attrs("30vw")
