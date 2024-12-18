
import yaml
import os


run_files = os.listdir('./Config/run_files/')
root_dir = os.getcwd()
with open('tags_out.csv', 'w') as outf:
    for f in run_files:
        os.chdir(root_dir)
        f_path = './Config/run_files/' + f
        with open(f_path) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            params = config['dataset']['layer_params']
            source = config['dataset']['source']
            if params['spatial_data'] == True:
                if source['is_simple'] == True:
                    title = params['title']
                    tags = params['tags']
                    tags = tags.replace(',',';')
                    layer_name = source['table_name']
                    outf.write(f"{layer_name}, {tags}\n")
                    print(f"{layer_name} -- {tags}")