import yaml
import os

def header_string():
    str = '{| class="wikitable"}\n! Dataset Name\n! Is it Spatial?\n! Date Last Updated (per layer metadata)\n'
    return(str)


def footer_string():
    str = '|}'
    return(str)


def bool_to_str(b):
    str=""
    if b:
        str="yes"
    return(str)


dir = './Config/run_files'
output_file = './wiki.txt'
with open(output_file, "w") as f_out:
    f_out.write(header_string())
    for filename in os.listdir(dir):
        if filename.endswith(".yml"):
            with open(os.path.join(dir, filename), "r") as f_in:
                f_out.write('|-\n')
                data = yaml.load(f_in, Loader=yaml.Loader)
                title = data.get("dataset",{}).get("layer_params", {}).get("title", "")
                title_string = "| {}".format(title)
                f_out.write(title_string + "\n")
                spatial_yn = data.get("dataset",{}).get("layer_params", {}).get("spatial_data","")
                spatial_string = "| {}".format(bool_to_str(spatial_yn))
                f_out.write(spatial_string + "\n")
                dlu = data.get("dataset",{}).get("layer_params", {}).get("metadata", {}).get("date_last_updated","")
                dlu = "| {}".format(dlu)
                f_out.write(dlu + "\n")
                #f_out.write("| \n")
    f_out.write(footer_string())