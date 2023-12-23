import re
import os
import json

import time
import shutil
import platform
import threading
import subprocess
import pandas

from urllib.parse import urlparse
from flask_cors import CORS
from flask import Flask, request, Response

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
        if len(os.listdir(link_dir)) == 0:
            yield "Being crawled..."
        else:
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
                print(output.strip())
                match = re.search(rb'SpiderProgress (\[mActive=\d+, mCompleted=\d+, mWaiting=\d+, mCompleted=\d+\.\d+%\])', output)
                if match:
                    # print(f"Progress: {match.group(1).decode()}")
                    yield match.group(1).decode()
                else:
                    continue
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

    addresses_no_h1 = df[(df['H1-1 Length'] == 0) & df['Address'].isin(adresses_indexable)]['Address'].tolist()
    adresses_h1 = df[(df['H1-1 Length'] > 0) & df['Address'].isin(adresses_indexable)][['Address', 'H1-1 Length']].values.tolist()

    addresses_no_title = df[(df['Title 1 Pixel Width'] == 0) & df['Address'].isin(adresses_indexable)]['Address'].tolist()
    addresses_title = df[(df['Title 1 Pixel Width'] > 0) & df['Address'].isin(adresses_indexable)][['Address', 'Title 1 Pixel Width']].values.tolist()

    adresses_meta_desc_doublon = df[df.duplicated(['Meta Description 1'], keep=False) & df['Address'].isin(adresses_indexable)]['Address'].tolist()

    non_canonical = df[df['Canonical Link Element 1'].isnull() & df['Address'].isin(adresses_indexable)]['Address'].tolist()
    self_canonical = df[(df['Canonical Link Element 1'] == df['Address']) & df['Address'].isin(adresses_indexable)]['Address'].tolist()
    external_canonical = df[(df['Canonical Link Element 1'] != df['Address']) & (df['Canonical Link Element 1'].notna()) & df['Address'].isin(adresses_indexable)]['Address'].tolist()

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
                "No H1": {
                    "Number": len(addresses_no_h1),
                    "Adresses": addresses_no_h1
                },
                "H1": {
                    "Number": len(adresses_h1),
                    "Adresses, Lenght": adresses_h1
                }
            },
            "Title Lenght": {
                "No Title": {
                    "Number": len(addresses_no_title),
                    "Adresses": addresses_no_title
                },
                "Ttile": {
                    "Number": len(addresses_title),
                    "Adresses": addresses_title
                }
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
    return "C'est pas la Kevin ^^ mets /start_crawl"
    
@app.route('/start_crawl', methods=['GET'])
def start_crawl():
    # link = "https://www.dynergie.fr/"
    # link = "https://inmodemd.fr/"
    link = request.args.get('link')
    print(f"Starting crawl for {link}")
    def generate():
        for progress in run_screaming_frog(link):
            if progress:
                if progress == "Being crawled...":
                    yield f"data:{progress}\n\n"
                yield f"data:{progress}\n\n"
                time.sleep(1)
            if not progress:
                info = get_screamingfrog_info(link)
                yield json.dumps(info)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/delete_crawl', methods=['GET'])
def delete_crawl():
    link = request.args.get('link')
    site_name = urlparse(link).netloc.replace("www.", "")
    link_dir = os.path.join("Saved-Sites", site_name)
    if os.path.isdir(link_dir):
        shutil.rmtree(link_dir)
        return "Crawl deleted"
    else:
        return "Crawl not found", 404

if __name__ == '__main__':
    if system == "Windows":
        app.run(debug=True)
    elif system == "Linux":
        app.run(host='0.0.0.0', port=9567)
