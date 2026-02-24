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
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.ticker import MaxNLocator
import xarray as xr
import shutil
import copernicusmarine

# -----------------------------
# 1️⃣ Configuración de carpetas
# -----------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data/NC_copernicus")
out_dir  = os.path.join(base_dir, "figures")

os.makedirs(data_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

# -----------------------------
# 2️⃣ Login Copernicus (usando secrets en GitHub Actions)
# -----------------------------
COPERNICUS_USERNAME = os.environ.get("COPERNICUS_USERNAME")
COPERNICUS_PASSWORD = os.environ.get("COPERNICUS_PASSWORD")

if not COPERNICUS_USERNAME or not COPERNICUS_PASSWORD:
    raise ValueError("COPERNICUS_USERNAME y COPERNICUS_PASSWORD deben estar definidos como secrets")

copernicusmarine.login(username=COPERNICUS_USERNAME, password=COPERNICUS_PASSWORD)

# -----------------------------
# 3️⃣ Descargar datos
# -----------------------------
thetao_file = os.path.join(data_dir, "thetao.nc")
cur_file    = os.path.join(data_dir, "currents.nc")

# Temperatura
if not os.path.exists(thetao_file):
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        variables=["thetao"],
        minimum_longitude=-16.5,
        maximum_longitude=-13,
        minimum_latitude=26.2,
        maximum_latitude=29.5,
        start_datetime="2026-02-01",
        end_datetime="2026-02-01",
        minimum_depth=0,
        maximum_depth=1,
        output_filename="thetao.nc",
        output_directory=data_dir
    )

# Corrientes
if not os.path.exists(cur_file):
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
        variables=["uo", "vo"],
        minimum_longitude=-16.5,
        maximum_longitude=-13,
        minimum_latitude=26.2,
        maximum_latitude=29.5,
        start_datetime="2026-02-01",
        end_datetime="2026-02-01",
        minimum_depth=0,
        maximum_depth=1,
        output_filename="currents.nc",
        output_directory=data_dir
    )

# -----------------------------
# 4️⃣ Abrir datasets
# -----------------------------
ds_sst = xr.open_dataset(thetao_file)
ds_cur = xr.open_dataset(cur_file)

# -----------------------------
# 5️⃣ Límites de la región
# -----------------------------
lat_min, lat_max = 26.2, 29.5
lon_min, lon_max = -16.5, -13

# -----------------------------
# 6️⃣ Recortar superficie y primera fecha
# -----------------------------
sst = ds_sst["thetao"].isel(time=0, depth=0)
uo  = ds_cur["uo"].isel(time=0, depth=0)
vo  = ds_cur["vo"].isel(time=0, depth=0)

lons = ds_sst["longitude"].values
lats = ds_sst["latitude"].values

lat_idx = (lats >= lat_min) & (lats <= lat_max)
lon_idx = (lons >= lon_min) & (lons <= lon_max)

sst_crop = sst.values[np.ix_(lat_idx, lon_idx)]
uo_crop  = uo.values[np.ix_(lat_idx, lon_idx)]
vo_crop  = vo.values[np.ix_(lat_idx, lon_idx)]

lon2d, lat2d = np.meshgrid(lons[lon_idx], lats[lat_idx])

date_str = str(np.datetime_as_string(ds_sst.time.values[0], unit='D'))
print("Procesando fecha:", date_str)

# -----------------------------
# 7️⃣ Generar figura
# -----------------------------
fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

# SST
pcm = ax.pcolormesh(lon2d, lat2d, sst_crop, cmap='turbo', shading='auto', transform=ccrs.PlateCarree())

# Corrientes (submuestreo)
step = 4
q = ax.quiver(lon2d[::step, ::step], lat2d[::step, ::step],
              uo_crop[::step, ::step], vo_crop[::step, ::step],
              scale=1, scale_units='inches', width=0.0025, color='black',
              transform=ccrs.PlateCarree())

ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s", labelpos='E', coordinates='axes', fontproperties={'size':10})

# Tierra y costa
ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)

# Gridlines
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.7, linestyle='--')
gl.top_labels = False
gl.right_labels = False
gl.xlocator = MaxNLocator(integer=True)
gl.ylocator = MaxNLocator(integer=True)

ax.set_title(f"SST + Surface Currents – {date_str}", fontsize=14)

cbar = plt.colorbar(pcm, orientation='vertical', pad=0.02, aspect=25)
cbar.set_label("Sea Surface Temperature (°C)", fontsize=12)

plt.tight_layout()

# -----------------------------
# 8️⃣ Guardar figura como latest.png
# -----------------------------
latest_path = os.path.join(out_dir, "latest.png")
fig.savefig(latest_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print(f"Figura generada y guardada en {latest_path}")