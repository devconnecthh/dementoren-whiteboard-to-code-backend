#!/usr/bin/env python3

"""
Taken from https://gist.github.com/igniteflow/5436066
"""
import http.server
import cgi
from pprint import pformat
import os
import shutil
import random
import string

from classes.inference.Sampler import *


OUTPUT_FOLDER="_out"
if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
# make sure you downloaded the model and weights as per scripts/get_pretrained_model.sh
SAMPLER = Sampler(model_json_path="../bin/model_json.json",
                      model_weights_path = "../bin/weights.h5")

PORT = 8080

BASE62_CHARSET=string.ascii_lowercase + string.digits + string.ascii_uppercase

def rand_string(n=8, charset=BASE62_CHARSET):
    res = ""
    for i in range(n):
        res += random.choice(charset)
    return res

class MyHandler(http.server.BaseHTTPRequestHandler):

    """
    For more information on CORS see:
    * https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS
    * http://enable-cors.org/
    """
    def do_OPTIONS(self):
        print("OPTIONS")
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def do_POST(self, *args, **kwargs):
        print("POST")
        try:
            # save file
            form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE":   self.headers['Content-Type']
            })
            _, ext = os.path.splitext(form["file"].filename)
            fname = rand_string() + ext
            while os.path.isfile(fname):
                fname = rand_string() + ext
            fdst = open(fname, "wb")
            shutil.copyfileobj(form["file"].file, fdst)
            fdst.close()
            print("saved " + fname)

            # call AI
            print("computing...")
            sampler.convert_single_image(OUTPUT_FOLDER, png_path=fname, print_generated_output=0,
            get_sentence_bleu=0, original_gui_filepath=None, style='default')
            print("done.")

            # FIXME will this work only with PNG ?
            file_to_serve = OUTPUT_FOLDER + "/" + fname.replace("png", "html")

            print("to serve: " +file_to_serve);

            # read response file
            body = ''
            with open(file_to_serve, "rb") as f:
                body = f.read()

            # set headers
            self.send_response(200)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", str(len(body)))
            self.end_headers()

            # write response body
            self.wfile.write(body)
        except Exception as e:
            print(e)

    def do_GET(self, *args, **kwargs):
        print("GET")
        """ just for testing """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        body = ''
        with open("../../wireframe.html","rb") as f:
            body = f.read()
        self.wfile.write(body)


def httpd(handler_class=MyHandler, server_address=('0.0.0.0', PORT), file_=None):
    try:
        print("Server started on http://%s:%s/" % (server_address[0], server_address[1]))
        srvr = http.server.HTTPServer(server_address, handler_class)
        srvr.serve_forever()  # serve_forever
    except KeyboardInterrupt:
        srvr.socket.close()


if __name__ == "__main__":
    """ ./corsdevserver.py """
    httpd()
    
