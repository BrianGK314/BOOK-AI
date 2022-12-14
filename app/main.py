from flask import Flask, render_template, request, Response
from apiclient.discovery import build
from bs4 import BeautifulSoup
import requests
import time
import json
import os
import logging
import asyncio


import logging
import traceback

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException



UPLOAD_FOLDER = "app/images"
app = Flask(__name__)


logger = logging.getLogger()

@app.errorhandler(HTTPException)
def handle_http_exception(error):
    error_dict = {
        'code': error.code,
        'description': error.description,
        'stack_trace': traceback.format_exc() 
    }
    log_msg = f"HTTPException {error_dict.code}, Description: {error_dict.description}, Stack trace: {error_dict.stack_trace}"
    logger.log(msg=log_msg)
    response = jsonify(error_dict)
    response.status_code = error.code
    return response


app.logger.setLevel(logging.ERROR)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/text',methods=['GET'])
def text():
    return render_template('concepttype.html')

@app.route('/text',methods=['POST'])
def text_predict():
    name_by_user = request.form['textfil']

    G_Key=os.GKEY

    resource = build("customsearch","v1",developerKey=G_Key).cse()

    #Contains the search term
    result = resource.list(q=name_by_user, cx=os.KEYST).execute()

    #name of book
    name,sum,avg_rating,page_link=web_items_user_text(result)

    #returns a list of ratings(number) and review.
    a=data(page_link)

    return render_template('concepttype.html', prediction=name,summary=sum,rev=a,avgrat=avg_rating)



@app.route('/',methods=['POST','GET'])
def predict():

    if request.method == 'POST':

        try:
            imagefile= request.files['imagefile']
        except:
            return "cannot find image!"
        
        try:
            image_path = "app/images/" + imagefile.filename
            imagefile.save(image_path)
        except:
            return "cannot save image!"

        try:
            api=os.API
            text= img_to_text_azure(api,image_path)

        except:
            return "Image to text api not working"

        #retrieve image

        try:
            resource = build("customsearch","v1",developerKey=os.PASS).cse()
            time.sleep(2)
        except:
            return "google search (build) not working"



        #Contains the search term

        try:
            result = resource.list(q=text[:153], cx=os.CX).execute()
            time.sleep(2)

        except:
            return "google resource not working"

        try:
            name,sum,avg_rating,page_link= web_items(result,resource,text)
        except:
            return "web items not working"


        #returns a list of ratings(number) and review.
        a=data(page_link)

        time.sleep(4)
        df()
        

        return render_template('index.html', prediction=name,summary=sum,rev=a,avgrat=avg_rating)
    else:
        no_prediction =True
        return render_template('index.html', no_prediction=no_prediction)

import os,shutil
import requests
from bs4 import BeautifulSoup

import time
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import json


def listToString(s): 
    str1 = " " 
    return (str1.join(s))


def web_items_user_text(result):
  name =result['items'][0]['htmlTitle']
  if '<b>' in name:
      name = name.replace('<b>','')
      name = name.replace('</b>','')

  if '&#39;' in name:
      name = name.replace('&#39;',"'")

  sum = result['items'][0]['snippet']

  try:
      avg_rating=result['items'][0]['pagemap']['aggregaterating'][0]['ratingvalue']
  except:
  #    avg_rating='pass'
      link=result['items'][0]['formattedUrl']
      source = requests.get(link)
      soup = BeautifulSoup(source.content, 'html.parser')

      a1=soup.find('div',class_='uitext stacked')

      avg_rating= a1.find_all('span')[-4].text.strip()


  #PART 2
  page_link=result['items'][0]['link']

  return name,sum,avg_rating,page_link


def web_items(result,resource,text):
    cx_t=os.CX
    if int(result['searchInformation']['totalResults']) ==0:
        result = resource.list(q=text[:int(len(text)*0.75)], cx=os.CX).execute()
        print('retry1')
        if int(result['searchInformation']['totalResults']) ==0:
            result = resource.list(q=text[int(len(text)*0.25):], cx=cx_t).execute()
            print('retry2')
            if int(result['searchInformation']['totalResults']) ==0:
                result = resource.list(q=text[int(len(text)*0.25):], cx=cx_t).execute()
                print('retry3')

    #name of book
    name =result['items'][0]['htmlTitle']
    if '<b>' in name:
        name = name.replace('<b>','')
        name = name.replace('</b>','')

    if '&#39;' in name:
        name = name.replace('&#39;',"'")

    cover=str(name)
    sum = result['items'][0]['snippet']

    try:
        try: 
            avg_rating=result['items'][0]['pagemap']['aggregaterating'][0]['ratingvalue']
        except KeyError:
            #Gets the rating of the next movie independent of whether they are closely related or not
            avg_rating=result['items'][1]['pagemap']['aggregaterating'][0]['ratingvalue']
    except:
        link=result['items'][0]['link']
        source = requests.get(link)
        soup = BeautifulSoup(source.content, 'html.parser')

        a1=soup.find('div',class_='uitext stacked')
        avg_rating= a1.find_all('span')[-4].text.strip()

    avg_rating


    #PART 2
    page_link=result['items'][0]['link']

    return name,sum,avg_rating,page_link


def df():
#remember to put "\" after predicted to indicate that you are entering into the "pred" folder inside the "image" folder!!!!!!
  folder = "app/images"
  for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))




def get_name(resp):
  resp= resp
  text=[]
  for i in range(len(resp)):
      text.append(resp[i]['text'])

  book_name=listToString(text)

  word = book_name.split()

  for i in word:
    if word.count(i) > 1:
      word.remove(i)

  book_name=listToString(word)
  return book_name



def data(link):
  source = requests.get(link)
  soup = BeautifulSoup(source.content, 'html.parser')
  #All the reviews
  all_reviews=soup.findAll('div',class_='friendReviews elementListBrown')[:9]

  #To translate digits
  trans={'did not like it':1,'it was ok':2,'liked it':3,'really liked it':4,'it was amazing':5}


  ult_list=[]
  for reveiw in all_reviews:
      
      #getting someones review
      next=reveiw.findAll('div','reviewText stacked')
      review= next[0].findAll('span')[-1].text

      #getting the rating someone gave to a book
      ratining_div=reveiw.findAll('span','staticStars notranslate')
      isRating=len(ratining_div)

      if review[0] != '[' and isRating>0:
          text=ratining_div[0].text.strip()
          rating=trans[text]

          ult_list.append([rating,str(review[:434]+'...')])

  return ult_list


def img_to_text_azure(api, image_path):
    cv_client=ComputerVisionClient("https://bookcomp.cognitiveservices.azure.com/",CognitiveServicesCredentials(api))
    response=cv_client.read_in_stream(open(image_path,'rb'),language='en',raw='True')
    oplocation=response.headers['Operation-Location']
    opid=oplocation.split('/')[-1]
    time.sleep(3.3)
    result=cv_client.get_read_result(opid)

    text=[]
    if (result.status) == OperationStatusCodes.succeeded:
        read_results=result.analyze_result.read_results
        for analysed_result in read_results:
            for line in analysed_result.lines:
                text.append(line.text)
                

    final_text = listToString(text)

    return final_text

