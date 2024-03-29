import obspy
import numpy as np
from os.path import join
import click


def get_tensor_dict(event_xml):
    result = {}
    for item in obspy.read_events(event_xml):
        id = item.preferred_origin().resource_id.id.split("/")[2]
        tensor = item.focal_mechanisms[0].moment_tensor.tensor
        latitude = item.preferred_origin().latitude
        longitude = item.preferred_origin().longitude
        depth = item.preferred_origin().depth
        result[id] = (tensor, longitude, latitude, depth)
    return result


def split_tensor_exponent(tensor):
    result = {}
    search_list = np.array(
        [tensor.m_rr, tensor.m_tt, tensor.m_pp, tensor.m_rt, tensor.m_rp, tensor.m_tp])
    search_list = np.abs(search_list)
    ref = np.min(search_list)

    exp = len(str(int(ref)))-1
    result = {
        "m_rr": tensor.m_rr/(10**exp),
        "m_tt": tensor.m_tt/(10**exp),
        "m_pp": tensor.m_pp/(10**exp),
        "m_rt": tensor.m_rt/(10**exp),
        "m_rp": tensor.m_rp/(10**exp),
        "m_tp": tensor.m_tp/(10**exp),
        "exp": exp
    }
    return result


@click.command()
@click.option('--gcmt', required=True, type=str)
@click.option('--output', required=True, type=str)
@click.option('--text/--no-text', default=False)
def main(gcmt, output, text):
    gcmt_dir = join("..", "..", "cmts", gcmt)
    output_path = join("..", "generated", output)
    tensor_dict = get_tensor_dict(join(gcmt_dir, "*"))
    with open(output_path, "w") as f:
        for key in tensor_dict:
            item, longitude, latitude, depth = tensor_dict[key]
            tensor = split_tensor_exponent(item)
            if(text):
                f.write(
                    f'{longitude} {latitude} {depth/1000:.2f} {tensor["m_rr"]:.3f} {tensor["m_tt"]:.3f} {tensor["m_pp"]:.3f} {tensor["m_rt"]:.3f} {tensor["m_rp"]:.3f} {tensor["m_tp"]:.3f} {tensor["exp"]} 0 0 {key}\n')
            else:
                f.write(
                    f'{longitude} {latitude} {depth/1000:.2f} {tensor["m_rr"]:.3f} {tensor["m_tt"]:.3f} {tensor["m_pp"]:.3f} {tensor["m_rt"]:.3f} {tensor["m_rp"]:.3f} {tensor["m_tp"]:.3f} {tensor["exp"]} 0 0 \n')


if __name__ == "__main__":
    main()
