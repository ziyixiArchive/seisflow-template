"""
Read in the frechet deritive of the source and add to the raw cmtsolution,
"""
import obspy
import numpy as np
import configparser
from os.path import join, basename, dirname, abspath
import pyproj
import click


def load_configure(config_fname):
    current_file_dir = dirname(abspath(__file__))
    config_path = join(current_file_dir, "..", "configuration", config_fname)
    config = configparser.ConfigParser()
    config.read(config_path)
    # load configs
    src_frechet_path = config["path"]["src_frechet"]
    cmtsolution_path = config["path"]["cmtsolution"]
    output_path = config["path"]["output"]
    max_dxs_ratio = float(config["setting"]["max_dxs_ratio"])
    return src_frechet_path, cmtsolution_path, output_path, max_dxs_ratio


def load_cmtsolution(cmtsolution_path):
    """
    Read in CMTSOLUTION
    """
    cmtsolution = obspy.read_events(cmtsolution_path)[0]
    return cmtsolution


def add_src_frechet(src_frechet_path, cmtsolution, max_dxs_ratio,output_path):
    """
    Read in and normalize src_frechet
    """
    data = np.loadtxt(src_frechet_path)
    # convert from dyne*cm to N*m
    dchi_dmt = np.array([
        [data[0], data[3], data[4]],
        [data[3], data[1], data[5]],
        [data[4], data[5], data[2]]
    ])*1e7
    dchi_dxs = np.array([
        data[6],
        data[7],
        data[8]
    ])
    # do the normalization as in tao's sem_utils
    # the final result will be the same regardless the factor
    cmt_tensor = cmtsolution.focal_mechanisms[0].moment_tensor.tensor
    mt = np.array([[cmt_tensor.m_rr, cmt_tensor.m_rt, cmt_tensor.m_rp],
                   [cmt_tensor.m_rt, cmt_tensor.m_tt, cmt_tensor.m_tp],
                   [cmt_tensor.m_rp, cmt_tensor.m_tp, cmt_tensor.m_pp]])
    m0 = (0.5*np.sum(mt**2))**0.5
    cc = np.sum(dchi_dmt*mt)/np.sum(mt**2)**0.5/np.sum(dchi_dmt**2)**0.5
    R_earth = 6371000.0
    dchi_dxs_ratio = R_earth * dchi_dxs
    dchi_dmt_ratio = m0 * dchi_dmt

    # ====== scale CMT gradient
    scale_factor = max_dxs_ratio/(np.sum(dchi_dxs_ratio**2))**0.5
    dxs_ratio = scale_factor * dchi_dxs_ratio
    dmt_ratio = scale_factor * dchi_dmt_ratio
    dxs = R_earth * dxs_ratio
    dmt = m0 * dmt_ratio

    # * add to the raw CMTSOLUTION
    # firstly we have to rely on x,y,z to convert the coordinate (not a sphere)
    geod = pyproj.Geod(ellps='WGS84')
    ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    lat = cmtsolution.preferred_origin().latitude
    lon = cmtsolution.preferred_origin().longitude
    alt = -cmtsolution.preferred_origin().depth
    x, y, z = pyproj.transform(lla, ecef, lon, lat, alt)
    r = (x**2 + y**2 + z**2)**0.5
    # get rotation matrix
    theta = np.arccos(z/r)
    phi = np.arctan2(y, x)
    sthe = np.sin(theta)
    cthe = np.cos(theta)
    sphi = np.sin(phi)
    cphi = np.cos(phi)
    # coordinate transformation matrix (r,theta,phi) to (x,y,z) 
    a = np.array(
    [ [ sthe*cphi, cthe*cphi, -1.0*sphi ],
      [ sthe*sphi, cthe*sphi,      cphi ],
      [ cthe     , -1.0*sthe,      0.0  ] ])
    # dr,dtheta,dphi to dx,dy,dz
    dxs_xyz=np.dot(a,dxs)
    x+=dxs_xyz[0]
    y+=dxs_xyz[1]
    z+=dxs_xyz[2]
    lon, lat, alt = pyproj.transform(ecef, lla, x, y, z)
    # add dmt
    mt+=dmt
    # we have to get mt at the new position
    mt_xyz=np.dot(np.dot(a, mt), np.transpose(a))
    # get new a at new x,y,z
    r = (x**2 + y**2 + z**2)**0.5
    theta = np.arccos(z/r)
    phi = np.arctan2(y, x)
    sthe = np.sin(theta)
    cthe = np.cos(theta)
    sphi = np.sin(phi)
    cphi = np.cos(phi)
    a = np.array(
    [ [ sthe*cphi, cthe*cphi, -1.0*sphi ],
      [ sthe*sphi, cthe*sphi,      cphi ],
      [ cthe     , -1.0*sthe,      0.0  ] ])
    # convert back to mt
    mt = np.dot(np.dot(np.transpose(a), mt_xyz), a)


    # write to the new CMTSOLUTION
    cmtsolution_new=cmtsolution.copy()
    cmtsolution_new.preferred_origin().latitude=lat
    cmtsolution_new.preferred_origin().longitude=lon
    cmtsolution_new.preferred_origin().depth=-alt
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_rr=mt[0,0]
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_tt=mt[1,1]
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_pp=mt[2,2]
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_rt=mt[1,0]
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_rp=mt[2,0]
    cmtsolution_new.focal_mechanisms[0].moment_tensor.tensor.m_tp=mt[2,1]
    cmtsolution_new.write(output_path,format="CMTSOLUTION")


@click.command()
@click.option('--conf', required=True, type=str, help="configuration file name in the configuration directory")
def main(conf):
    src_frechet_path, cmtsolution_path, output_path, max_dxs_ratio = load_configure(
        conf)
    cmtsolution = load_cmtsolution(cmtsolution_path)
    add_src_frechet(src_frechet_path, cmtsolution, max_dxs_ratio,output_path)


if __name__ == "__main__":
    main()
