import re
import os
import json
import time
import platform
import threading
import subprocess
import pandas

from urllib.parse import urlparse
from flask import Flask, request, Response

app = Flask(__name__)

system = platform.system()
print(f"Running System: {system}")

def run_screaming_frog(link):
    if system == "Windows":
        base_output_path = r"C:\Users\youss\OneDrive\Desktop\Github\super-waffle\Saved-Sites"
        cwd = r'C:\Program Files (x86)\Screaming Frog SEO Spider'
    elif system == "Linux":
        base_output_path = r"/home/ubuntu/yosuuu/super-waffle/Saved-Sites"
        cwd = None
    else:
        raise Exception("System not supported, can you please select Windows or Linux")
    
    site_name = urlparse(link).netloc.replace("www.", "")
    link_dir = os.path.join(base_output_path, site_name)
    
    if os.path.isdir(link_dir):
        print(f"{site_name} already crawled")
        yield
    else:
        os.makedirs(link_dir, exist_ok=True)
        output_path = link_dir
        
        command = fr'screamingfrogseospider --headless --crawl {link} --export-tabs "Internal:HTML" --save-crawl --output-folder "{output_path}" --overwrite'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                match = re.search(rb'SpiderProgress (\[mActive=\d+, mCompleted=\d+, mWaiting=\d+, mCompleted=\d+\.\d+%\])', output)
                if match:
                    print(f"Progress: {match.group(1).decode()}")
                    yield match.group(1).decode()
        rc = process.poll()

        if rc != 0:
            stderr = process.stderr.read()
            yield f"Error occurred: {stderr.decode()}"
        else:
            yield

def get_screamingfrog_info(link): 
    site_name = urlparse(link).netloc.replace("www.", "")
    df = pandas.read_csv(os.path.join("Saved-Sites", site_name, "internal_html.csv"))
    
    adresses_200 = df[df['Status Code'] == 200]['Address'].tolist()
    adresses_404 = df[df['Status Code'] == 404]['Address'].tolist()
    adresses_301 = df[df['Status Code'] == 301]['Address'].tolist()
    
    adresses_indexable = df[df['Indexability'] == 'Indexable']['Address'].tolist()
    adresses_not_indexable = df[df['Indexability'] == 'Non-Indexable']['Address'].tolist()

    addresses_miss_h1, adresses_more_than_0_lenght = df[df['H1-1 Length'] == 0]['Address'].tolist(), df[df['H1-1 Length'] > 0][['Address', 'H1-1 Length']].values.tolist()
    addresses_title_more_561px = df[df['Title 1 Pixel Width'] > 561]['Address'].tolist()
    
    adresses_meta_desc_doublon = df[df.duplicated(['Meta Description 1'], keep=False)]['Address'].tolist()
    
    non_canonical = df[df['Canonical Link Element 1'].isnull()]['Address'].tolist()
    self_canonical = df[df['Canonical Link Element 1'] == df['Address']]['Address'].tolist()
    external_canonical = df[(df['Canonical Link Element 1'] != df['Address']) & (df['Canonical Link Element 1'].notna())]['Address'].tolist()

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
            "H1 Lenght": {
                "Missing H1": {
                    "Number": len(addresses_miss_h1),
                    "Adresses": addresses_miss_h1
                },
                "H1 > 0": {
                    "Number": len(adresses_more_than_0_lenght),
                    "Adresses, Lenght": adresses_more_than_0_lenght
                }
            },
            "Title > 561px": {
                "Number": len(addresses_title_more_561px),
                "Adresses": addresses_title_more_561px
            },
            "Indexability": {
                "Indexable": {
                    "Number": len(adresses_indexable),
                    "Adresses": adresses_indexable
                },
                "Not Indexable": {
                    "301": {
                        "Number": len(adresses_301),
                        "Adresses": adresses_301
                    },
                    "404": {
                        "Number": len(adresses_404),
                        "Adresses": adresses_404
                    },
                    "External Canonical": {
                        "Number": len(external_canonical),
                        "Adresses": external_canonical
                    },
                    "Number 301 + 404 + External Canonical": len(adresses_301) + len(adresses_404) + len(external_canonical),
                    "Number others": len(adresses_not_indexable) - (len(adresses_301) + len(adresses_404) + len(external_canonical)),
                    "Total Not Indexable": len(adresses_not_indexable)
                }
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
def index():
    return "C'est pas la Kevin ^^ mets /start_process"

    
@app.route('/start_process', methods=['POST', 'GET'])
def start_process():
    # link = "https://www.dynergie.fr/"
    # link = "https://inmodemd.fr/"
    link = request.args.get('link')
    print(f"Starting process for {link}")
    def generate():
        for progress in run_screaming_frog(link):
            if progress:
                yield f"data:{progress}\n\n"
                time.sleep(1)
            if not progress:
                info = get_screamingfrog_info(link)
                yield json.dumps(info)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    if system == "Windows":
        app.run(debug=True)
    elif system == "Linux":
        app.run(host='0.0.0.0', port=9567)
