import os
import time
import base64
import platform
import requests

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException

now = datetime.now()
current_time = now.strftime("%H-%M-%S")

timeout = 10

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-remote-fonts")
chrome_options.add_argument("--lang=zh-TW")

screenshots_path = '/screenshots/'
if platform.system() == 'Windows':
  driver = webdriver.Chrome(r'chromedriver', chrome_options=chrome_options)
  screenshots_path = 'c:\\windows\\temp\\'
else:
  driver = webdriver.Chrome(r'/opt/chrome/chromedriver', chrome_options=chrome_options)

driver.fullscreen_window()
driver.get("https://xs.teamxports.com/xs03.aspx?module=login_page&files=login")
# accept alert all the time
driver.switch_to.alert.accept()

def captchaImg2Text(captchaImg, apiKey):
    with open(captchaImg, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        url = 'https://api.apitruecaptcha.org/one/gettext'

        data = {
            'userid': 'jonas.cheng@gmail.com',
            'apikey': apiKey,
            'data': encoded_string
        }
        response = requests.post(url=url, json=data)
        data = response.json()
        return data

def Login():
    print("%s | Login" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'subform_List')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # debug purpose
    # html = driver.page_source
    # print(html)

    # download captcha
    img_base64 = driver.execute_script("""
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width; cnv.height = ele.height;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    """, driver.find_element(By.ID, 'ContentPlaceHolder1_CaptchaImage'))

    captchaImg = '%s%s-captcha.png' % (screenshots_path, current_time)
    with open(captchaImg, 'wb') as image:
        image.write(base64.b64decode(img_base64))

    # convert Img to Text
    jsonData = captchaImg2Text(captchaImg, os.environ['APIKEY'])
    if 'result' in jsonData:
        captchaText = jsonData['result']
    else:
        print('unexpected jsonData %s' % jsonData)
        raise Exception('unexpected jsonData %s' % jsonData)

    # input login id
    login_id_input = driver.find_element(By.ID, 'ContentPlaceHolder1_loginid')
    login_id_input.send_keys(os.environ['ID'])

    # input password
    password_input = driver.find_element(By.ID, 'loginpw')
    password_input.send_keys(os.environ['PSWD'])

    # input captcha
    captcha_input = driver.find_element(By.ID, 'ContentPlaceHolder1_Captcha_text')
    captcha_input.send_keys(captchaText)

    # debug purpose
    if not driver.save_screenshot('%s%s-Login.png' % (screenshots_path, current_time)):
        print('save Login failed')

    # click on login btn
    login_btn = driver.find_element(By.ID, 'login_but')
    login_btn.click()

    print("%s | Login successfully" % driver.title)


def WantBookBadminton():
    print("%s | WantBookBadminton" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_button_image')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookBadminton.png' % (screenshots_path, current_time)):
        print('save WantBookBadminton failed')

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[title='羽球']")
    badminton_btn.click()

def AgreeEula():
    print("%s | AgreeEula" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[src='img/conf01.png']")))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # debug purpose
    if not driver.save_screenshot('%s%s-AgreeEula.png' % (screenshots_path, current_time)):
        print('save AgreeEula failed')

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[src='img/conf01.png']")
    badminton_btn.click()

    # accept alert
    driver.switch_to.alert.accept()

def WantBookDate():
    print("%s | WantBookDate" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_StepImage_Lab')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookDate.png' % (screenshots_path, current_time)):
        print('save WantBookDate failed')

    # execute script to select date
    driver.execute_script("""
    var date = arguments[0];
    GoToStep2(date, '1');
    """, '2023/03/10')

def WantBookTime():
    print("%s | WantBookTime" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step2_data')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookTime.png' % (screenshots_path, current_time)):
        print('save WantBookTime failed')

    # execute script to select afternoon
    driver.execute_script("""
    var date = arguments[0];
    GoToStep2(date, '2');
    """, '2023/03/10')

    # select all "PlaceBtn"
    btns = driver.find_elements(By.CSS_SELECTOR, "img[name='PlaceBtn']")
    for btn in btns:
        # print(btn.get_attribute("onclick"))
        if '12:00~13:00' in btn.get_attribute("onclick"):
            btn.click()
            # accept alert
            driver.switch_to.alert.accept()
            break

def SaveResult():
    print("%s | SaveResult" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step3Info_lab')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    time.sleep(timeout)
    if not driver.save_screenshot('%s%s-Result.png' % (screenshots_path, current_time)):
        print('save Result failed')

# calcuate book date, now + 13day

# check if

# login page
Login()
# want book badminton
WantBookBadminton()
# agress eula
AgreeEula()
# want book date
WantBookDate()
# want book time
WantBookTime()
# save result
SaveResult()

# terminate driver session and close all windows
driver.quit()
