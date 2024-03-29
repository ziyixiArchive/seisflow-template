from misfit_windows import Misfit_window
import obspy
from os.path import join, basename, dirname, abspath
import configparser
import pickle
from window import Window, Windows_collection
import pyasdf
import click


def load_configure(config_fname):
    current_file_dir = dirname(abspath(__file__))
    config_path = join(current_file_dir, "..", "configuration", config_fname)
    config = configparser.ConfigParser()
    config.read(config_path)
    # load configs
    windows_dir = config["path"]["windows_dir"]
    first_arrival_dir = config["path"]["first_arrival_dir"]
    baz_dir = config["path"]["baz_dir"]
    data_asdf_body_path = config["path"]["data_asdf_body_path"]
    sync_asdf_body_path = config["path"]["sync_asdf_body_path"]
    data_asdf_surface_path = config["path"]["data_asdf_surface_path"]
    sync_asdf_surface_path = config["path"]["sync_asdf_surface_path"]
    output_dir = config["path"]["output_dir"]
    used_gcmtid = config["setting"]["used_gcmtid"]
    consider_surface = config["setting"].getboolean("consider_surface")
    use_tqdm = config["setting"].getboolean("use_tqdm")
    return (windows_dir, first_arrival_dir, baz_dir, data_asdf_body_path, sync_asdf_body_path,
            data_asdf_surface_path, sync_asdf_surface_path, output_dir, used_gcmtid, consider_surface, use_tqdm)


def load_pickle(pickle_path):
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    return data


def prepare_windows(windows, used_gcmtid, consider_surface):
    """
    Generate misfit windows and split different component from the windows.
    """
    new_windows = {}
    windows_used_event = windows[used_gcmtid]
    for net_sta in windows_used_event:
        if(consider_surface):
            new_windows[net_sta] = {
                "z": Windows_collection(),
                "r": Windows_collection(),
                "t": Windows_collection(),
                "surface_z": Windows_collection(),
                "surface_r": Windows_collection(),
                "surface_t": Windows_collection()
            }
        else:
            new_windows[net_sta] = {
                "z": Windows_collection(),
                "r": Windows_collection(),
                "t": Windows_collection()
            }
        old_windows_z = windows_used_event[net_sta]["z"].windows
        old_windows_r = windows_used_event[net_sta]["r"].windows
        old_windows_t = windows_used_event[net_sta]["t"].windows
        if(consider_surface):
            old_windows_surface_z = windows_used_event[net_sta]["surface_z"].windows
            old_windows_surface_r = windows_used_event[net_sta]["surface_r"].windows
            old_windows_surface_t = windows_used_event[net_sta]["surface_t"].windows
        # update to the new_windows
        for each_window in old_windows_z:
            new_windows[net_sta]["z"].append_window(
                Misfit_window(each_window))
        for each_window in old_windows_r:
            new_windows[net_sta]["r"].append_window(
                Misfit_window(each_window))
        for each_window in old_windows_t:
            new_windows[net_sta]["t"].append_window(
                Misfit_window(each_window))
        if (consider_surface):
            for each_window in old_windows_surface_z:
                new_windows[net_sta]["surface_z"].append_window(
                    Misfit_window(each_window))
            for each_window in old_windows_surface_r:
                new_windows[net_sta]["surface_r"].append_window(
                    Misfit_window(each_window))
            for each_window in old_windows_surface_t:
                new_windows[net_sta]["surface_t"].append_window(
                    Misfit_window(each_window))
    return new_windows


def calculate_snr_cc_deltat(data_asdf_body_path, sync_asdf_body_path, data_asdf_surface_path, sync_asdf_surface_path, misfit_windows, first_arrival_zr, first_arrival_t, baz, use_tqdm):
    data_asdf_body = pyasdf.ASDFDataSet(data_asdf_body_path)
    sync_asdf_body = pyasdf.ASDFDataSet(sync_asdf_body_path)
    data_asdf_surface = pyasdf.ASDFDataSet(data_asdf_surface_path)
    sync_asdf_surface = pyasdf.ASDFDataSet(sync_asdf_surface_path)
    if (use_tqdm):
        import tqdm
        for net_sta in tqdm.tqdm(misfit_windows, total=len(misfit_windows)):
            for category in misfit_windows[net_sta]:
                for each_window in misfit_windows[net_sta][category].windows:
                    # update the first arrival
                    if(each_window.channel == "Z" or each_window.channel == "R"):
                        each_window.update_first_arrival_baz(
                            first_arrival_zr, baz)
                    elif (each_window.channel == "T"):
                        each_window.update_first_arrival_baz(
                            first_arrival_t, baz)
                    else:
                        raise Exception(
                            "channel not correct in updating the first arrival!")
                    # update snr,deltat and cc
                    if((category == "z") or (category == "r") or (category == "t")):
                        each_window.update_snr(data_asdf_body,sync_asdf_body)
                        each_window.update_cc_deltat(
                            data_asdf_body, sync_asdf_body)
                    elif((category == "surface_z") or (category == "surface_r") or (category == "surface_t")):
                        each_window.update_snr(data_asdf_surface,sync_asdf_body)
                        each_window.update_cc_deltat(
                            data_asdf_surface, sync_asdf_surface)
                    else:
                        raise Exception(
                            "category is not correct in calculatng snr,delta and cc")
    else:
        for net_sta in misfit_windows:
            for category in misfit_windows[net_sta]:
                for each_window in misfit_windows[net_sta][category].windows:
                    # update the first arrival
                    if(each_window.channel == "Z" or each_window.channel == "R"):
                        each_window.update_first_arrival_baz(
                            first_arrival_zr, baz)
                    elif (each_window.channel == "T"):
                        each_window.update_first_arrival_baz(
                            first_arrival_t, baz)
                    else:
                        raise Exception(
                            "channel not correct in updating the first arrival!")
                    # update snr,deltat and cc
                    if((category == "z") or (category == "r") or (category == "t")):
                        each_window.update_snr(data_asdf_body,sync_asdf_body)
                        each_window.update_cc_deltat(
                            data_asdf_body, sync_asdf_body)
                    elif((category == "surface_z") or (category == "surface_r") or (category == "surface_t")):
                        each_window.update_snr(data_asdf_surface,sync_asdf_body)
                        each_window.update_cc_deltat(
                            data_asdf_surface, sync_asdf_surface)
                    else:
                        raise Exception(
                            "category is not correct in calculatng snr,delta and cc")
    del data_asdf_body
    del sync_asdf_body
    del data_asdf_surface
    del sync_asdf_surface
    return misfit_windows


def save_misfit_windows(misfit_windows, output_dir, used_gcmtid):
    output_path = join(output_dir, f"{used_gcmtid}.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(misfit_windows, f)


def run(windows_dir, first_arrival_dir, baz_dir, data_asdf_body_path, sync_asdf_body_path,
        data_asdf_surface_path, sync_asdf_surface_path, output_dir, used_gcmtid, consider_surface, use_tqdm):
    # load windows
    windows = load_pickle(join(windows_dir, "windows.pkl"))
    # prepare windows
    misfit_windows = prepare_windows(windows, used_gcmtid, consider_surface)
    # calculate snr,cc,deltat
    first_arrival_zr_path = join(first_arrival_dir, "traveltime.P.pkl")
    first_arrival_t_path = join(first_arrival_dir, "traveltime.S.pkl")
    baz_path = join(baz_dir, "extra.baz.pkl")
    first_arrival_zr = load_pickle(first_arrival_zr_path)
    first_arrival_t = load_pickle(first_arrival_t_path)
    baz = load_pickle(baz_path)
    misfit_windows = calculate_snr_cc_deltat(data_asdf_body_path, sync_asdf_body_path, data_asdf_surface_path,
                                             sync_asdf_surface_path, misfit_windows, first_arrival_zr, first_arrival_t, baz, use_tqdm)
    save_misfit_windows(misfit_windows, output_dir, used_gcmtid)


@click.command()
@click.option('--conf', required=True, type=str, help="configuration file name in the configuration directory")
def main(conf):
    config_path = join("..", "configuration", conf)
    windows_dir, first_arrival_dir, baz_dir, data_asdf_body_path, sync_asdf_body_path, data_asdf_surface_path, sync_asdf_surface_path, output_dir, used_gcmtid, consider_surface, use_tqdm = load_configure(
        config_path)
    run(windows_dir, first_arrival_dir, baz_dir, data_asdf_body_path, sync_asdf_body_path,
        data_asdf_surface_path, sync_asdf_surface_path, output_dir, used_gcmtid, consider_surface, use_tqdm)


if __name__ == "__main__":
    main()
