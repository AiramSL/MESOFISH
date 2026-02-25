#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 18:03:29 2026

@author: airamsarmiento
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script_auto.py
Descarga automáticamente datos de Copernicus (thetao y corrientes),
recorta la región de Canarias, genera la figura SST + Surface Currents
y guarda latest.png listo para la web.
"""
import os
import copernicusmarine
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.ticker import MaxNLocator
import xarray as xr
from datetime import datetime
import pandas as pd

today = datetime.utcnow().strftime("%Y-%m-%d")

# -----------------------------
# Login Copernicus
# -----------------------------
copernicusmarine.login(
    username=os.environ.get("COPERNICUS_USERNAME"),
    password=os.environ.get("COPERNICUS_PASSWORD")
)

#out_dir = "data/NC_copernicus"
#os.makedirs(out_dir, exist_ok=True)

# Descargar thetao
ds_sst = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
    variables=["thetao"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)

ds_cur = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
    variables=["uo", "vo"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)



# -----------------------------
# Seleccionar superficie
# -----------------------------
sst = ds_sst["thetao"].isel(time=0, depth=0)
uo  = ds_cur["uo"].isel(time=0, depth=0)
vo  = ds_cur["vo"].isel(time=0, depth=0)

lons = ds_sst["longitude"].values
lats = ds_sst["latitude"].values

lon2d, lat2d = np.meshgrid(lons, lats)

date_str = str(np.datetime_as_string(ds_sst.time.values[0], unit='D'))

# -----------------------------
# Crear figura
# -----------------------------
fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-16.5, -13, 26.2, 29.5], crs=ccrs.PlateCarree())

pcm = ax.pcolormesh(
    lon2d, lat2d, sst.values,
    cmap='turbo', shading='auto',
    transform=ccrs.PlateCarree()
)

step = 4
q = ax.quiver(
    lon2d[::step, ::step],
    lat2d[::step, ::step],
    uo.values[::step, ::step],
    vo.values[::step, ::step],
    scale=1,
    scale_units='inches',
    width=0.0025,
    color='black',
    transform=ccrs.PlateCarree()
)

ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s",
             labelpos='E', coordinates='axes',
             fontproperties={'size':10})

ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)

gl = ax.gridlines(draw_labels=True, linewidth=0.5,
                  color='gray', alpha=0.7, linestyle='--')
gl.top_labels = False
gl.right_labels = False
gl.xlocator = MaxNLocator(integer=True)
gl.ylocator = MaxNLocator(integer=True)

ax.set_title(f"SST + Surface Currents – {date_str}", fontsize=14)

cbar = plt.colorbar(pcm, orientation='vertical', pad=0.02, aspect=25)
cbar.set_label("Sea Surface Temperature (°C)", fontsize=12)

plt.tight_layout()

# -----------------------------
# Guardar figura
# -----------------------------
out_path = "figures"
os.makedirs(out_path, exist_ok=True)

latest_path = os.path.join(out_path, "latest.png")
fig.savefig(latest_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como latest.png")





##### serie temporal


# Abrir dataset
ds_bgc = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_glo_bgc_my_0.083deg-lmtl_P1D-i",
    variables=["zooc", "npp", "mnkc_epi"],
    minimum_longitude=-15.2976,
    maximum_longitude=-15.2976,
    minimum_latitude=28.1617,
    maximum_latitude=28.1617,
    start_datetime="2020-01-01",  # la fecha más lejana disponible
    end_datetime="2026-02-01"
)

# Extraer series temporales del punto
time = ds_bgc.time.values
zooc = ds_bgc["zooc"].isel(latitude=0, longitude=0).values
npp  = ds_bgc["npp"].isel(latitude=0, longitude=0).values
mnkc = ds_bgc["mnkc_epi"].isel(latitude=0, longitude=0).values

# Crear DataFrame para gráfico
df = pd.DataFrame({
    "Date": pd.to_datetime(time),
    "Zooplankton (g/m²)": zooc,
    "NPP (mg/m²/day)": npp,
    "Epipelagic micronekton (g/m²)": mnkc
})
df.set_index("Date", inplace=True)

# Graficar
# Suponiendo que df tiene columnas: "zooc", "mnkc_epi", "npp" y "time"
fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10,12), sharex=True)

# Panel 1: Zooplancton
# Panel 1: Zooplancton
axes[0].plot(df.index, df["Zooplankton (g/m²)"], marker='o', linestyle='-')
axes[0].set_ylabel("Zooplankton [g/m²]")
axes[0].set_title("Serie temporal en Lon=-15.2976, Lat=28.1617")
axes[0].grid(True)

# Panel 2: Epipelagic micronekton
axes[1].plot(df.index, df["Epipelagic micronekton (g/m²)"], marker='o', linestyle='-', color='orange')
axes[1].set_ylabel("Epipelagic micronekton [g/m²]")
axes[1].grid(True)

# Panel 3: NPP
axes[2].plot(df.index, df["NPP (mg/m²/day)"], marker='o', linestyle='-', color='green')
axes[2].set_ylabel("Net Primary Productivity [mg/m²/day]")
axes[2].set_xlabel("Fecha")
axes[2].grid(True)

plt.tight_layout()


SERIE_path = os.path.join(out_path, "series_temporal_point.png")
fig.savefig(SERIE_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Serie temporal guardada como series_temporal_point.png")






