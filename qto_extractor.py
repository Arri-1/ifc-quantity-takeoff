import ifcopenshell
import ifcopenshell.util.element as el_util
import pandas as pd
import ifcopenshell.util.unit as u
import ifcopenshell.geom, ifcopenshell.util.shape

IFC_FILE = "sample.ifc"
ELEMENT_TYPES = ["IfcBeam", "IfcColumn", "IfcSlab", "IfcWall", "IfcFooting"]
VOLUME_KEYS = ("NetVolume", "GrossVolume", "Volume")

def get_volume(element):
    """Look through the element's quantity sets for a volume value."""
    for qto in el_util.get_psets(element, qtos_only=True).values():
        for key in VOLUME_KEYS:
            if key in qto and qto[key] is not None:
                return float(qto[key])
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, element)
    volume = ifcopenshell.util.shape.get_volume(shape.geometry)
    return volume

def get_material_name(element):
    mats = el_util.get_materials(element)
    return ", ".join(m.Name for m in mats if m.Name) or "Unknown"

model = ifcopenshell.open(IFC_FILE)
print(u.calculate_unit_scale(model))
rows = []

for ifc_type in ELEMENT_TYPES:
    for element in model.by_type(ifc_type):
        rows.append({
            "GlobalId": element.GlobalId,
            "Type": ifc_type,
            "Name": element.Name,
            "Material": get_material_name(element),
            "Volume_m3": get_volume(element),
        })

df = pd.DataFrame(rows)
print(f"Elements found: {len(df)}, with volume: {df['Volume_m3'].notna().sum()}")

# Bill of Quantities: total volume per element type and material
boq = (df.dropna(subset=["Volume_m3"])
         .groupby(["Type", "Material"], as_index=False)["Volume_m3"].sum()
         .round(2))

# Total concrete (material name contains 'concrete' or 'beton')
is_concrete = df["Material"].str.contains("concrete|beton", case=False, na=False)
total_concrete = df.loc[is_concrete, "Volume_m3"].sum()
print(f"Total concrete volume: {total_concrete:.2f} m3")

df.to_csv("elements_detail.csv", index=False)
boq.to_csv("bill_of_quantities.csv", index=False)
print(boq)