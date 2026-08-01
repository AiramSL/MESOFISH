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
import pandas as pd

from datetime import datetime, UTC

today = datetime.now(UTC).strftime("%Y-%m-%d")

# -----------------------------
# Login Copernicus
# -----------------------------
copernicusmarine.login(
    username=os.environ.get("COPERNICUS_USERNAME"),
    password=os.environ.get("COPERNICUS_PASSWORD")
)

#out_dir = "data/NC_copernicus"
#os.makedirs(out_dir, exist_ok=True)

# -----------------------------
#  1️⃣  Serie temporal zooplankton, mnkc, NPP
# -----------------------------
ds_bgc = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_glo_bgc_my_0.083deg-lmtl_P1D-i",
    variables=["zooc","npp","mnkc_epi"],
    minimum_longitude=-15.2976,
    maximum_longitude=-15.2976,
    minimum_latitude=28.1617,
    maximum_latitude=28.1617,
    start_datetime="2020-01-01",
    end_datetime=today
)
time = ds_bgc.time.values
zooc = ds_bgc["zooc"].isel(latitude=0, longitude=0).values
npp  = ds_bgc["npp"].isel(latitude=0, longitude=0).values
mnkc = ds_bgc["mnkc_epi"].isel(latitude=0, longitude=0).values
df = pd.DataFrame({
    "Date": pd.to_datetime(time),
    "Zooplankton (g/m²)": zooc,
    "Epipelagic micronekton (g/m²)": mnkc,
    "NPP (mg/m²/day)": npp
})

df.set_index("Date", inplace=True)

fig, axes = plt.subplots(3,1, figsize=(10,12), sharex=True)
axes[0].plot(df.index, df["Zooplankton (g/m²)"], marker='o'); axes[0].set_ylabel("Zooplankton [g/m²]"); axes[0].grid(True)
axes[1].plot(df.index, df["Epipelagic micronekton (g/m²)"], marker='o', color='orange'); axes[1].set_ylabel("Micronekton [g/m²]"); axes[1].grid(True)
axes[2].plot(df.index, df["NPP (mg/m²/day)"], marker='o', color='green'); axes[2].set_ylabel("NPP [mg/m²/day]"); axes[2].set_xlabel("Fecha"); axes[2].grid(True)
plt.tight_layout()

# -----------------------------
# Guardar figura
# -----------------------------

out_path = "figures"
os.makedirs(out_path, exist_ok=True)

SERIE_path = os.path.join(out_path, "series_temporal_point.png")
fig.savefig(SERIE_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Serie temporal guardada como series_temporal_point.png")




# -----------------------------
# 2️⃣ SST + Corrientes superficiales
# -----------------------------
ds_sst = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m",
    variables=["thetao"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)

ds_cur = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m",
    variables=["uo","vo"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)

sst = ds_sst["thetao"].isel(time=0, depth=0)
uo  = ds_cur["uo"].isel(time=0, depth=0)
vo  = ds_cur["vo"].isel(time=0, depth=0)
lons = ds_sst["longitude"].values
lats = ds_sst["latitude"].values
lon2d, lat2d = np.meshgrid(lons, lats)
date_str = str(np.datetime_as_string(ds_sst.time.values[0], unit='D'))

fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-16.5, -13, 26.2, 29.5], crs=ccrs.PlateCarree())
pcm = ax.pcolormesh(lon2d, lat2d, sst.values, cmap='turbo', shading='auto', transform=ccrs.PlateCarree())
step = 4
q = ax.quiver(lon2d[::step,::step], lat2d[::step,::step],
              uo.values[::step,::step], vo.values[::step,::step],
              scale=1, scale_units='inches', width=0.0025, color='black',
              transform=ccrs.PlateCarree())
ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s", labelpos='E', coordinates='axes', fontproperties={'size':10})
ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)
gl = ax.gridlines(draw_labels=True, linewidth=0)
gl.top_labels = False
gl.right_labels = False
gl.left_labels = True
gl.bottom_labels = True

ax.set_title(f"SST + Surface Currents – {date_str}", fontsize=14)
cbar = plt.colorbar(pcm, orientation='vertical', pad=0.02, aspect=25)
cbar.set_label("Sea Surface Temperature (°C)", fontsize=12)
plt.tight_layout()


# -----------------------------
# Guardar figura
# -----------------------------


latest_path = os.path.join(out_path, "latest.png")
fig.savefig(latest_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como latest.png")


# -----------------------------
# 3️⃣ SST + flujo geostrófico
# -----------------------------
ds_SSH = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_phy-ssh_anfc_detided-0.027deg_P1D-m",
    variables=["zos_detided"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)
ssh = ds_SSH["zos_detided"].isel(time=0).values

# Calcular flujo geostrófico
lons = ds_SSH["longitude"].values
lats = ds_SSH["latitude"].values
lon2d, lat2d = np.meshgrid(lons, lats)
phi = np.deg2rad(lat2d)
f = 2*7.2921e-5*np.sin(phi)
dlat = np.deg2rad(lats[1]-lats[0])
dlon = np.deg2rad(lons[1]-lons[0])
dy = 6371000*dlat
dx = 6371000*np.cos(phi)*dlon
dssh_dy = np.gradient(ssh, axis=0)/dy
dssh_dx = np.gradient(ssh, axis=1)/dx
ugeo = -9.81/f*dssh_dy
vgeo = 9.81/f*dssh_dx

fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-16.5,-13,26.2,29.5], crs=ccrs.PlateCarree())
pcm = ax.pcolormesh(lon2d, lat2d, ds_sst["thetao"].isel(time=0, depth=0).values,
                    cmap='turbo', shading='auto', transform=ccrs.PlateCarree())
step = 4
q = ax.quiver(lon2d[::step,::step], lat2d[::step,::step], ugeo[::step,::step], vgeo[::step,::step],
              scale=1, scale_units='inches', width=0.0025, color='black', transform=ccrs.PlateCarree())
ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s", labelpos='E', coordinates='axes', fontproperties={'size':10})
ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)
gl = ax.gridlines(draw_labels=True, linewidth=0)
gl.top_labels = False
gl.right_labels = False
gl.left_labels = True
gl.bottom_labels = True
plt.title(f"SST + Geostrophic Currents – {date_str}")
plt.colorbar(pcm, label="SST [°C]")
plt.tight_layout()


# -----------------------------
# Guardar figura
# -----------------------------

SSTgeo_path = os.path.join(out_path, "SSTgeo.png")
fig.savefig(SSTgeo_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como SSTgeo.png")




# -----------------------------
# 4️⃣ CHL + flujo geostrófico
# -----------------------------
### el que usabamos "cmems_obs-oc_atl_bgc-plankton_my_l4-gapfree-multi-1km_P1D"
ds_CHL = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_bgc_anfc_0.027deg-3D_P1D-m",
    variables=["chl"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime="2026-02-16",
    end_datetime=today
)
time_chl = pd.to_datetime(ds_CHL.time.values)
last_date_chl = time_chl.max()
ds_CHL_day = ds_CHL.sel(time=last_date_chl)
lons_chl = ds_CHL_day["longitude"].values
lats_chl = ds_CHL_day["latitude"].values
lon2d_chl, lat2d_chl = np.meshgrid(lons_chl, lats_chl)

#chl = ds_CHL_day["chl"].values
chl = ds_CHL_day["chl"].sel(depth=0, method="nearest").values

## Crear figura
fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([lons_chl.min(), lons_chl.max(), lats_chl.min(), lats_chl.max()], crs=ccrs.PlateCarree())

# Colormesh de CHL usando paleta de SST ('turbo')
# Definir rango de colores según percentiles para no ser afectado por valores extremos
vmin = np.nanpercentile(chl, 5)    # valor por debajo del 5% se pone al mínimo color
vmax = np.nanpercentile(chl, 95)  # valor por encima del 95% se pone al máximo color

pcm = ax.pcolormesh(
    lon2d_chl, lat2d_chl, chl,
    cmap='jet', shading='auto',
    vmin=vmin, vmax=vmax,  # aquí ajustas la paleta
    transform=ccrs.PlateCarree()
)

# Interpolar flujo geostrófico a la malla de CHL
import xarray as xr

ugeo_da = xr.DataArray(ugeo, coords=[ds_sst.latitude, ds_sst.longitude], dims=["latitude", "longitude"])
vgeo_da = xr.DataArray(vgeo, coords=[ds_sst.latitude, ds_sst.longitude], dims=["latitude", "longitude"])

ugeo_interp = ugeo_da.interp(latitude=lats_chl, longitude=lons_chl)
vgeo_interp = vgeo_da.interp(latitude=lats_chl, longitude=lons_chl)

# Quiver
step = 5  # submuestreo para no saturar flechas
q = ax.quiver(
    lon2d_chl[::step, ::step],
    lat2d_chl[::step, ::step],
    ugeo_interp.values[::step, ::step],
    vgeo_interp.values[::step, ::step],
    scale=1, scale_units='inches', width=0.0025, color='black',
    transform=ccrs.PlateCarree()
)

ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s", labelpos='E', coordinates='axes', fontproperties={'size':10})

# Añadir costa y tierra
ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)

# Gridlines: solo izquierda y abajo
gl = ax.gridlines(draw_labels=True, linewidth=0)
gl.top_labels = False
gl.right_labels = False
gl.left_labels = True
gl.bottom_labels = True

# Título
ax.set_title(f"Chlorophyll + Geostrophic Currents – {last_date_chl.strftime('%Y-%m-%d')}")

# Colorbar
cbar = plt.colorbar(pcm, label="Chlorophyll [mg/m³]")

plt.tight_layout()



# -----------------------------
# Guardar figura
# -----------------------------

CHLgeo_path = os.path.join(out_path, "CHLgeo.png")
fig.savefig(CHLgeo_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como CHLgeo.png")




#### SSH

# -----------------------------
# SSH dataset
# -----------------------------
ds_SSH = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_phy-ssh_anfc_detided-0.027deg_P1D-m",
    variables=["zos_detided"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    start_datetime=today,
    end_datetime=today
)

ssh = ds_SSH["zos_detided"].isel(time=0).values
lons_ssh = ds_SSH["longitude"].values
lats_ssh = ds_SSH["latitude"].values
lon2d_ssh, lat2d_ssh = np.meshgrid(lons_ssh, lats_ssh)

# -----------------------------
# Reinterpolar flujo geostrófico si es necesario
# -----------------------------
# ugeo, vgeo vienen del SST o de tu cálculo geostrófico
ugeo_da = xr.DataArray(ugeo, coords=[ds_sst.latitude, ds_sst.longitude], dims=["latitude", "longitude"])
vgeo_da = xr.DataArray(vgeo, coords=[ds_sst.latitude, ds_sst.longitude], dims=["latitude", "longitude"])

ugeo_interp = ugeo_da.interp(latitude=lats_ssh, longitude=lons_ssh)
vgeo_interp = vgeo_da.interp(latitude=lats_ssh, longitude=lons_ssh)

# -----------------------------
# Crear figura
# -----------------------------
fig = plt.figure(figsize=(8,6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([lons_ssh.min(), lons_ssh.max(), lats_ssh.min(), lats_ssh.max()], crs=ccrs.PlateCarree())

# SSH
pcm = ax.pcolormesh(
    lon2d_ssh, lat2d_ssh, ssh,
    cmap='RdYlBu_r', shading='auto',
    transform=ccrs.PlateCarree()
)

# Flechas geostróficas
step = 4  # ajustar según densidad de flechas
q = ax.quiver(
    lon2d_ssh[::step, ::step], lat2d_ssh[::step, ::step],
    ugeo_interp.values[::step, ::step], vgeo_interp.values[::step, ::step],
    scale=1, scale_units='inches', width=0.0025,
    color='black', transform=ccrs.PlateCarree()
)

ax.quiverkey(q, 0.88, 0.04, 0.5, "0.5 m/s", labelpos='E', coordinates='axes', fontproperties={'size':10})

# Tierra y costa
ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgrey')
ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.2)

# Gridlines (solo etiquetas izquierda y abajo)
gl = ax.gridlines(draw_labels=True, linewidth=0)
gl.top_labels = False
gl.right_labels = False
gl.left_labels = True
gl.bottom_labels = True

# Título y colorbar
date_str = str(np.datetime_as_string(ds_SSH.time.values[0], unit='D'))
ax.set_title(f"SSH + Geostrophic Flow – {date_str}", fontsize=14)

cbar = plt.colorbar(pcm, orientation='vertical', pad=0.02, aspect=25)
cbar.set_label("Sea Surface Height [m]", fontsize=12)

plt.tight_layout()


# -----------------------------
# Guardar figura
# -----------------------------

SSHgeo_path = os.path.join(out_path, "SSHgeo.png")
fig.savefig(SSHgeo_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como SSHgeo.png")






######## PERFEILES VERTICALES

import copernicusmarine
import xarray as xr
import matplotlib.pyplot as plt
from datetime import datetime, UTC

today = datetime.now(UTC).strftime("%Y-%m-%d")

# BIOGEOQUÍMICO
ds_BIO = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_bgc_anfc_0.027deg-3D_P1D-m",
    variables=["chl", "o2"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    minimum_depth=0.5,   # o 1.0, algo > 0.494...
    maximum_depth=1000,
    start_datetime=today,
    end_datetime=today
)

# FÍSICO
ds_PHY = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_ibi_phy_anfc_0.027deg-3D_P1D-m",
    variables=["thetao", "so", "mlotst"],
    minimum_longitude=-16.5,
    maximum_longitude=-13,
    minimum_latitude=26.2,
    maximum_latitude=29.5,
    minimum_depth=0.5,
    maximum_depth=1000,
    start_datetime=today,
    end_datetime=today
)

print("=== ds_BIO ===")
print("Dimensiones:", ds_BIO.dims)
print("Coordenadas:", list(ds_BIO.coords.keys()))
print("Variables:", list(ds_BIO.data_vars.keys()))

print("\n=== ds_PHY ===")
print("Dimensiones:", ds_PHY.dims)
print("Coordenadas:", list(ds_PHY.coords.keys()))
print("Variables:", list(ds_PHY.data_vars.keys()))



points = {
    "Point_1": {"lon": -15.25, "lat": 28.1005},
    "Point_2": {"lon": -15.7152, "lat": 27.6164}
}

def extract_profile(ds, lon, lat):
    return ds.sel(longitude=lon, latitude=lat, method="nearest").squeeze()

profiles = {}

# Extraer perfiles
for name, p in points.items():
    phy = extract_profile(ds_PHY, p["lon"], p["lat"])
    bio = extract_profile(ds_BIO, p["lon"], p["lat"])
    profiles[name] = xr.merge([phy, bio], compat="no_conflicts")




import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# UNA SOLA FIGURA con 2 paneles horizontales
fig = plt.figure(figsize=(16, 12))

# === PANEL A: Point_1 ===
ds_a = profiles["Point_1"]
depth_a = ds_a.depth
lon_a, lat_a = ds_a.longitude.values, ds_a.latitude.values

# Perfiles Panel A
ax_a = fig.add_axes([0.05, 0.12, 0.35, 0.72])  
ax_a.plot(ds_a.thetao, depth_a, color='steelblue', linewidth=4)
ax_a.set_xlabel('Temperature (°C)', fontsize=20, fontweight='bold')
ax_a.set_ylabel('Depth (m)', fontsize=20, fontweight='bold')
ax_a.invert_yaxis()
ax_a.set_ylim(1000, 0)
ax_a.tick_params(labelsize=16)
ax_a.grid(alpha=0.3, linewidth=1.2)
ax_a.text(-0.15, 1.02, '(A)', transform=ax_a.transAxes, fontsize=24, fontweight='bold')

# Ejes secundarios Panel A
ax_sal_a = ax_a.twiny()
ax_sal_a.plot(ds_a.so, depth_a, color='forestgreen', linewidth=4)
ax_sal_a.set_xlabel('Salinity', fontsize=20, fontweight='bold', color='forestgreen')
ax_sal_a.tick_params(axis='x', labelsize=16, labelcolor='forestgreen')

ax_o2_a = ax_a.twiny()
ax_o2_a.spines['top'].set_position(('outward', 45))
ax_o2_a.plot(ds_a.o2, depth_a, color='darkred', linewidth=4)
ax_o2_a.set_xlabel('O₂ (mol m⁻³)', fontsize=20, fontweight='bold', color='darkred')
ax_o2_a.tick_params(axis='x', labelsize=16, labelcolor='darkred')

ax_chl_a = ax_a.twiny()
ax_chl_a.spines['top'].set_position(('outward', 90))
ax_chl_a.plot(ds_a.chl, depth_a, color='purple', linewidth=4)
ax_chl_a.set_xlabel('Chl-a (mg m⁻³)', fontsize=20, fontweight='bold', color='purple')
ax_chl_a.tick_params(axis='x', labelsize=16, labelcolor='purple')

# Mapa Panel A
ax_map_a = fig.add_axes([0.15, 0.15, 0.27, 0.22], projection=ccrs.PlateCarree())
ax_map_a.set_extent([-15.9, -15.2, 27.5, 28.2], crs=ccrs.PlateCarree())
ax_map_a.add_feature(cfeature.COASTLINE, linewidth=1.0)
ax_map_a.add_feature(cfeature.LAND, facecolor='wheat', edgecolor='saddlebrown', linewidth=0.6)
ax_map_a.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.8)
ax_map_a.plot(lon_a, lat_a, 'ro', markersize=8, transform=ccrs.PlateCarree(), 
              markeredgecolor='darkred', markeredgewidth=1.5, zorder=10)
ax_map_a.text(0.5, 1.05, f'{today}', transform=ax_map_a.transAxes, 
              ha='center', va='bottom', fontsize=10, fontweight='bold',
              bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))

# === PANEL B: Point_2 ===
ds_b = profiles["Point_2"]
depth_b = ds_b.depth
lon_b, lat_b = ds_b.longitude.values, ds_b.latitude.values

# Perfiles Panel B  
ax_b = fig.add_axes([0.55, 0.12, 0.35, 0.72])
ax_b.plot(ds_b.thetao, depth_b, color='steelblue', linewidth=4)
ax_b.set_xlabel('Temperature (°C)', fontsize=20, fontweight='bold')
ax_b.invert_yaxis()
ax_b.set_ylim(1000, 0)
ax_b.tick_params(labelsize=16)
ax_b.grid(alpha=0.3, linewidth=1.2)
ax_b.text(-0.15, 1.02, '(B)', transform=ax_b.transAxes, fontsize=24, fontweight='bold')

# Ejes secundarios Panel B
ax_sal_b = ax_b.twiny()
ax_sal_b.plot(ds_b.so, depth_b, color='forestgreen', linewidth=4)
ax_sal_b.set_xlabel('Salinity', fontsize=20, fontweight='bold', color='forestgreen')
ax_sal_b.tick_params(axis='x', labelsize=16, labelcolor='forestgreen')

ax_o2_b = ax_b.twiny()
ax_o2_b.spines['top'].set_position(('outward', 45))
ax_o2_b.plot(ds_b.o2, depth_b, color='darkred', linewidth=4)
ax_o2_b.set_xlabel('O₂ (mol m⁻³)', fontsize=20, fontweight='bold', color='darkred')
ax_o2_b.tick_params(axis='x', labelsize=16, labelcolor='darkred')

ax_chl_b = ax_b.twiny()
ax_chl_b.spines['top'].set_position(('outward', 90))
ax_chl_b.plot(ds_b.chl, depth_b, color='purple', linewidth=4)
ax_chl_b.set_xlabel('Chl-a (mg m⁻³)', fontsize=20, fontweight='bold', color='purple')
ax_chl_b.tick_params(axis='x', labelsize=16, labelcolor='purple')

# Mapa Panel B
ax_map_b = fig.add_axes([0.65, 0.15, 0.27, 0.22], projection=ccrs.PlateCarree())
ax_map_b.set_extent([-15.9, -15.2, 27.5, 28.2], crs=ccrs.PlateCarree())
ax_map_b.add_feature(cfeature.COASTLINE, linewidth=1.0)
ax_map_b.add_feature(cfeature.LAND, facecolor='wheat', edgecolor='saddlebrown', linewidth=0.6)
ax_map_b.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.8)
ax_map_b.plot(lon_b, lat_b, 'ro', markersize=8, transform=ccrs.PlateCarree(), 
              markeredgecolor='darkred', markeredgewidth=1.5, zorder=10)
ax_map_b.text(0.5, 1.05, f'{today}', transform=ax_map_b.transAxes, 
              ha='center', va='bottom', fontsize=10, fontweight='bold',
              bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))

plt.tight_layout()
plt.show()


Perfil_path = os.path.join(out_path, "Profiles.png")
fig.savefig(Perfil_path, dpi=150, bbox_inches='tight')
plt.close(fig)

print("Figura guardada como Profiles.png")
