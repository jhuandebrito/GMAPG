from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

codigos_os = {
    'spdm': '263',
    'vivario': '264',
    'fas': '265',
    'cejam': '268',
    'riosaude': '9612',
    'gnosis': '9615',
    'ideias': '10040',
    'cieds': '10358',
    'htmj': '9803',
    'cruzvermelha': '9739',
    'fiotec': '259',
    'iabas': '261',
    'ciedsbrasil': '11225',
    'ipcep': '9900'
} 

# Clicar em elementos
def click_element(driver,element):
    driver.execute_script("arguments[0].click();", element)

def navegador():
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--log-level=3')
    driver = webdriver.Edge(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)

    return driver, wait

#Identificar as imagens dentro do anexo
def identificar_imagens(file_path):
    imagens = []

    try:
        df = pd.read_excel(file_path)        
    
    except Exception as e1:
        print('Error em abrir com excel: ', e1)
        try:
            df = pd.read_csv(file_path, sep=';')            
        
        except Exception as e2:
            print('Error no csv: ', e2)
            df = pd.read_csv(file_path, sep=';', encoding='latin1')
                

    if 'NOVO_VALOR' in df.columns:
        for valor in df['NOVO_VALOR'].unique():
            if '_' in str(valor):
                imagens.append(str(valor))
    
    elif 'DESCRICAO' in df.columns:
        for valor in df['DESCRICAO'].unique():
            if '_' in str(valor):
                imagens.append(str(valor))
    
    else:
        print("Nenhum campo que contem imagens foi encontrdado no arquivo")
    
    return imagens

#Navegar até a página da pesquisa de documento
def modulo_pesquisar(login, driver, wait):
    driver.get('https://osinfo.prefeitura.rio/Home.html')

    if login == False:
        try:
            usuario = wait.until(EC.presence_of_element_located((By.ID,'user')))
            senha = driver.find_element(By.ID,'password')

            usuario.send_keys('acesso')
            senha.send_keys('publico')

            senha.send_keys(Keys.ENTER)

            #print('Logado com sucesso')

            login = True
        except:
            print('Elementos de login nao localizados')
            return -1

    try:
        financeiro_drop = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mCSB_1_container"]/div/a[2]')))
        time.sleep(2)
        driver.execute_script("arguments[0].click();", financeiro_drop)        

    except:
        print('Error ao clicar no financeiro. Tentando novamente...')
        try:
            financeiro_drop = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mCSB_1_container"]/div/a[2]')))
            time.sleep(2)
            driver.execute_script("arguments[0].click();", financeiro_drop)   
        except:
            print('Error ao clicar no financeiro.')
            return -1
    
    try:
        pesquisarDoc_btn = wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="Doc"]')))

        time.sleep(1)

        driver.execute_script("arguments[0].click();", pesquisarDoc_btn)

    except:
        print('Error ao entrar na pesquisa de documentos')   
        return -1  

    return 0

#Procurar uma imagem no modulo de pesquisar imagem
def pesquisar_imagem(instituicao, driver, wait, action, imagem):
    resposta = ''

    imagem = imagem.replace('.pdf','')
    
    title = wait.until(EC.presence_of_element_located((By.ID,'unitLabel')))

    time.sleep(2)

    action.move_to_element(title).perform()

    action.send_keys(Keys.TAB).perform()

    action.send_keys(Keys.ENTER).perform()

    action.send_keys(instituicao).perform()

    time.sleep(2)

    action.send_keys(Keys.ENTER).perform()

    for nome in imagem.split(' '):
        if len(nome) > 5:
            document_name = wait.until(EC.presence_of_element_located((By.ID,'documentNameValue')))
            document_name.send_keys(nome)
            break

    pesquisar_btn = driver.find_element(By.ID,'documentSearch')

    driver.execute_script("arguments[0].click();", pesquisar_btn)

    select = Select(wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="documentTable_length"]/label/select'))))

    time.sleep(1)     

    select.select_by_value('-1')

    linha_1 = wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="documentTable"]/tbody/tr/td[1]')))

    time.sleep(1)

    conteudo = driver.find_element(By.XPATH,'//*[@id="documentTable"]/tbody')

    linhas = conteudo.find_elements(By.TAG_NAME,'tr')

    imgs = []

    for l in linhas:
        try:
            imgs.append(l.find_elements(By.TAG_NAME,'td')[1].text.replace('.pdf',''))
            #print(imgs)
        except:
            pass
            

    if imagem not in imgs:
        resposta = f'Imagem não encontrada: {imagem}'   
     
    else:
        resposta = f'Imagem encontrada com sucesso: {imagem}'
    
    voltar = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/div/button')
    driver.execute_script("arguments[0].click();", voltar)    

    return resposta

#Verificar se as imagens identificadas estão importadas no painel
def validar_imagens(instituicao,file_path):
    respostas = []

    login = False

    print('-Iniciando validaçao de imagens! ' + file_path)

    driver, wait = navegador()

    action = ActionChains(driver)

    try:
        imagens = identificar_imagens(file_path)
    
    except:
        respostas.append("Error na abertura do arquivo. Verifique se o arquivo está em csv ou xlsx, UTF-8.")
        return respostas   
    
    modulo_pesquisar(login, driver, wait)
    
    for imagem in imagens:
        while True:
            try:
                respostas.append(pesquisar_imagem(instituicao, driver, wait, action, imagem))
                break
            except:
                modulo_pesquisar(login,driver,wait)

    return respostas



