from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurações do Selenium
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Inicializa o driver do Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# URL inicial da página
url = "https://www.zarahome.com/es/bano-toallas-n1051"
driver.get(url)
time.sleep(5)  # Espera inicial para garantir que a página carregue

# Função para realizar scroll na página
def scroll_to_bottom():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Espera para o carregamento do conteúdo dinâmico
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        
def remove_overlay():
    overlays = [
        "newsletter-advice-dialog-container"
    ]
    
    for overlay_class in overlays:
        try:
            # Aguarda até que o overlay esteja presente
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, overlay_class))
            )
            # Localiza o overlay
            overlay = driver.find_element(By.CLASS_NAME, overlay_class)
            
            # Verifica se o overlay está visível
            if overlay.is_displayed():
                # Remove o overlay
                driver.execute_script("arguments[0].remove();", overlay)
                time.sleep(1)  # Espera para garantir que o overlay tenha sido removido
                break  # Encerra o loop após remover o primeiro overlay
        except Exception:
            # Não faz nada se o overlay não for encontrado ou não estiver visível
            pass

# Função para extrair informações detalhadas de cada produto
def extract_product_details():
    data = []  # Inicializando a lista de dados
    products = driver.find_elements(By.CLASS_NAME, "product-item-container")

    for index, product in enumerate(products):
        try:
            print(f"Processando produto {index + 1} de {len(products)}")

            # Espera até que o produto esteja clicável
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(product))

            # Rolagem para o produto para garantir que ele esteja visível
            driver.execute_script("arguments[0].scrollIntoView();", product)
            product.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-detail-content__product-name")))
            
            
            # Extração de dados
            title = driver.find_element(By.CLASS_NAME, "product-detail-content__product-name").text

            # Extraindo o preço (preço promocional e preço original)
            price_elements = driver.find_elements(By.CLASS_NAME, "price-single__current")

            if len(price_elements) > 0:
                prices = price_elements[0].find_elements(By.TAG_NAME, "span")
                if len(prices) == 2:
                    # Se houver dois preços, eles são considerados intervalo
                    price = f"{prices[0].text} - {prices[1].text}"

                elif len(prices) == 1:
                    # Caso haja apenas um preço
                    price = prices[0].text

                else:
                    price = "N/A"

            else:
                price = "N/A"

            # Extração de outras informações
            colors = [
                img.get_attribute("alt")
                for img in driver.find_elements(By.CLASS_NAME, "product-color-selector__color-image")
            ]
            
            description = driver.find_element(By.CLASS_NAME, "long-description").text
            
            weight = driver.find_element(By.CLASS_NAME, "grammage-info").find_element(By.TAG_NAME, "span").text

            sizes = [
                size.text
                for size in driver.find_elements(By.CLASS_NAME, "size-description__size")
            ]
            
            remove_overlay()

            # # Extraindo composição de materiais
            # composition_elements = driver.find_elements(By.CLASS_NAME, "composition__components")
            # composition_data = []
            
            # for composition in composition_elements:
            #     items = composition.find_elements(By.CLASS_NAME, "component-description")
            #     for item in items:
            #         composition_data.append(item.text.strip())  # Adiciona o texto da composição

            # composition = ", ".join(composition_data)  # Junta as composições em uma string separada por vírgulas

            # Print para depuração (exibe os valores de preço)
            print(f"Price: {price} | Original Price: {original_price}")
            
            # Adiciona os dados à lista
            data.append({
                "title": title,
                "price": price,
                "colors": ", ".join(colors),
                "description": description,
                "weight": weight,
                "sizes": ", ".join(sizes),
            })

            # Volta para a página inicial
            driver.back()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-item-container")))
            time.sleep(3)  # Espera para garantir que a página inicial recarregue
        except Exception as e:
            print(f"Erro ao processar produto {index + 1}: {e}")

    return data  # Retorna a lista com os dados extraídos

# Chama a função e armazena o resultado na variável `data`
data = extract_product_details()

# Salva os dados no arquivo CSV
with open("zarahome_products.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["title", "price", "original_price", "colors", "description", "weight", "sizes", "composition"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for row in data:
        writer.writerow(row)

print("Dados extraídos e salvos em zarahome_products.csv")

# Encerra o navegador
driver.quit()
