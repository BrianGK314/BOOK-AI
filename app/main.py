from flask import Flask, render_template, request
from comboutils import df, data, web_items, web_items_user_text,img_to_text_azure, img_to_text_ninja
from apiclient.discovery import build
from bs4 import BeautifulSoup
import requests
import time
import json

app = Flask(__name__)

@app.route('/text',methods=['GET'])
def text():
    return render_template('concepttype.html')

@app.route('/text',methods=['POST'])
def text_predict():
    name_by_user = request.form['textfil']

    G_Key='AIzaSyDQn27q-RrhCqsGgqzGFSdi1FeIKrqv_GA'

    resource = build("customsearch","v1",developerKey=G_Key).cse()

    #Contains the search term
    result = resource.list(q=name_by_user, cx="318f2d8e0346626fb").execute()

    #name of book
    name,sum,avg_rating,page_link=web_items_user_text(result)

    #returns a list of ratings(number) and review.
    a=data(page_link)

    return render_template('concepttype.html', prediction=name,summary=sum,rev=a,avgrat=avg_rating)

@app.route('/',methods=['GET'])
def home():
    no_prediction =True
    return render_template('index.html', no_prediction=no_prediction)


@app.route('/',methods=['POST'])
def predict():

    #Obtain image & Save
    imagefile= request.files['imagefile']
    image_path = "images/books/" + imagefile.filename
    imagefile.save(image_path)

    #Predict Image

    N_Key='hSplTYExlQlsw7/CanxVyg==UaVGwMyC16SefTzf'
    headers= {"X-Api-Key": N_Key}
    text = img_to_text_ninja(image_path, headers)

    # credential =json.load(open('credentials.json'))
    # api='57b40208aa58430d9877390c2130b351'
    # text= img_to_text_azure(api,image_path)

    resource = build("customsearch","v1",developerKey='AIzaSyDQn27q-RrhCqsGgqzGFSdi1FeIKrqv_GA').cse()



    #Contains the search term
    result = resource.list(q=text[:153], cx="318f2d8e0346626fb").execute()

    name,cover,sum,avg_rating,page_link= web_items(result,resource,text)

    #returns a list of ratings(number) and review.
    a=data(page_link)

    time.sleep(2)
    df()

    return render_template('index.html', prediction=name,summary=sum,rev=a,avgrat=avg_rating,bknm=cover)