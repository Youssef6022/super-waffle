import subprocess
import pandas as pd

from flask import Flask, request
app = Flask(__name__)

def run_screaming_frog(link, system="windows"):
    if system == "windows":
        output_path = r"C:\Users\youss\OneDrive\Desktop\Github\super-waffle"
        command = fr'screamingfrogseospider --headless --crawl {link} --export-tabs "Internal:HTML" --save-crawl --output-folder "{output_path}" --overwrite'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=r'C:\Program Files (x86)\Screaming Frog SEO Spider')
        stdout, stderr = process.communicate()
            
        if process.returncode != 0:
            return f"Error occurred: {stderr.decode()}"
        else:
            return "Success"
        
    if system == "linux":
        output_path = r"/home/ubuntu/yosuuu/super-waffle"
        command = fr'screamingfrogseospider --crawl {link} --headless --save-crawl --output-folder {output_path} --export-tabs "Internal:HTML" --overwrite'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
            
        if process.returncode != 0:
            return f"Error occurred: {stderr.decode()}"
        else:
            return "Success"
        
    else:
        raise Exception("System not supported, can you please select windows or linux")
    
def get_adresses_meta_desc_doublon(df):
    meta_description_dict = {}

    for index, row in df.iterrows():
        if row['Meta Description 1'] in meta_description_dict:
            meta_description_dict[row['Meta Description 1']].append(row['Address'])
        else:
            meta_description_dict[row['Meta Description 1']] = [row['Address']]
            
    adresses_meta_desc_doublon = []

    for meta_description, addresses in meta_description_dict.items():
        if len(addresses) > 1:
            adresses_meta_desc_doublon.extend(addresses)
            
    return adresses_meta_desc_doublon

def get_screamingfrog_info():
    df = pd.read_csv('internal_html.csv') 

    adresses_200 = []
    adresses_404 = []
    adresses_301 = []

    addresses_miss_h1 = []
    addresses_title_more_561px = []
    adresses_meta_desc_doublon = get_adresses_meta_desc_doublon(df)
    
    non_canonical = df[df['Canonical Link Element 1'].isnull()]['Address'].tolist()
    self_canonical = df[df['Canonical Link Element 1'] == df['Address']]['Address'].tolist()
    external_canonical = df[(df['Canonical Link Element 1'] != df['Address']) & (df['Canonical Link Element 1'].notna())]['Address'].tolist()

    for index, row in df.iterrows():
        if row['Status Code'] == 200:
            adresses_200.append(row['Address'])
        if row['Status Code'] == 404:
            adresses_404.append(row['Address'])
        if row['Status Code'] == 301:
            adresses_301.append(row['Address'])
            
        if row['H1-1 Length'] == 0:
            addresses_miss_h1.append(row['Address'])
            
        if row['Title 1 Pixel Width'] > 561:
            addresses_title_more_561px.append(row['Address'])
                
    json_data = {
        "Info": {
            "Number of Pages": len(df),
            "200": {
                "Number": len(adresses_200),
                "Adresses": adresses_200
            },
            "404": {
                "Number": len(adresses_404),
                "Adresses": adresses_404
            },
            "301": {
                "Number": len(adresses_301),
                "Adresses": adresses_301
            },
            "Missing H1": {
                "Number": len(addresses_miss_h1),
                "Adresses": addresses_miss_h1
            },
            "Title > 561px": {
                "Number": len(addresses_title_more_561px),
                "Adresses": addresses_title_more_561px
            },
            "Meta Description Doublon": {
                "Number": len(adresses_meta_desc_doublon),
                "Adresses": adresses_meta_desc_doublon
            },
            "Canonical": {
                "None Canonical": {
                    "Number": len(non_canonical),
                    "Adresses": non_canonical
                },
                "Self Canonical": {
                    "Number": len(self_canonical),
                    "Adresses": self_canonical
                },
                "External Canonical": {
                    "Number": len(external_canonical),
                    "Adresses": external_canonical
                }
            },
        }
    }
            
    return json_data
     
@app.route('/')
def get_info():
    link = request.args.get('link')
    # link = "https://inmodemd.fr/"
    print(f'recieve requested for {link}')
    scr_frog = run_screaming_frog(link, system="windows")
    
    if scr_frog == "Success":
        return get_screamingfrog_info()
    else:
        return scr_frog
    
if __name__ == '__main__':
    # app.run(debug=True) # windows
    app.run(host='0.0.0.0', port=9567) # linux
