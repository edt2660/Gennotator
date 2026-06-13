from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import requests
import json
import time
driver = webdriver.Chrome() 


def findPhages(page, perPage = 50):
    pListTemp = requests.get('https://phagesdb.org/api/sequenced_phages/', params = {"page": page, "page_size": perPage})
    print(pListTemp.status_code)
    pList = pListTemp.json()
    phages = []
    for item in pList["results"]:
        if (item["in_genbank"] == True):
            phages.append(item["phage_name"])
            print(item["phage_name"])
    print(len(phages))
    return(phages)


def getPhageAnnoGenes(names):
    results = []
    for name in names:
#        oneResult = []
#        oneResult.append(["name", name])
        n = 0
        geneSeqTemp = requests.get('https://phagesdb.org/api/genesbyphage/' + name + '/', params = {"page": 1, "page_size": 500})
        print(geneSeqTemp.status_code)  # 200 = ok, 404 = not found, 500 = server error 
        genes = geneSeqTemp.json()
        for element in genes["results"]:
            n += 1
            if element["Notes"] != "":
                fastaSeq = ""
                anno = element["Notes"]
                fastaSeq = ">" + name + "_" + str(n) + "\n" + element["Translation"]
                results.append([fastaSeq, anno])
                print(name + " " + str(n) + " " + anno + "\n" + fastaSeq) 
#        results.append(oneResult) turns out this oneResult thing was useless
    return results #results are the fasta, then the annotation
                
def hhpred (fasta, anno): #fasta list and anno list need to be in same order in terms of this fasta goes with this annotation
    hhpredResults = []
    driver.get("https://toolkit.tuebingen.mpg.de/tools/hhpred") #setting up site
    wait = WebDriverWait(driver, 900)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.multiselect__tags-wrap")) == 12)
    driver.execute_script("document.querySelector('div.Cookie--toolkit').style.display = 'none';")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "div.multiselect__tags-wrap")[0])
    keys = ["pfa", "uni", "ncb"]
    for e in keys:
        select = driver.find_elements(By.CSS_SELECTOR, "div.multiselect__select")[0]
        select.click()
        input_field = driver.find_element(By.CSS_SELECTOR, "div.multiselect__tags input")
        driver.execute_script("arguments[0].click();", input_field)
        input_field.send_keys(e)
        input_field.send_keys(Keys.ENTER)
        n = 0
    try:
        for entry in fasta: #iterate through every fasta 
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea")))
            entryBox = driver.find_elements(By.CSS_SELECTOR, "textarea")[0]
            while True:
                entryBox.clear()
                entryBox.send_keys(entry)
                wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "[data-v-step='submit']"))
                submit = driver.find_element(By.CSS_SELECTOR, "[data-v-step='submit']")
                submit.click()
                print(entry)
                print("queued")
                wait.until(lambda d: (
                    driver.execute_script("arguments[0].click();", d.find_elements(By.XPATH, "//button[contains(text(), 'Load existing job')]")[0])
                    if d.find_elements(By.XPATH, "//button[contains(text(), 'Load existing job')]") else None
                ) or d.find_elements(By.XPATH, "//h4[contains(text(), 'Hitlist')]") or d.find_elements(By.CSS_SELECTOR, "span.banner-message"))
                
                # check if we hit the error page
                if driver.find_elements(By.CSS_SELECTOR, "span.banner-message"):
                    driver.back()
                    driver.back()
                    continue  # restart the while loop
                else:
                    break  # success, exit the while loop
            
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr[role='row'][aria-rowindex='5']")))
            print("job complete")
            for x in range(1,11):
                row = driver.find_element(By.CSS_SELECTOR, "tr[role='row'][aria-rowindex='" + str(x) + "']")
                hhpredInfo = row.find_element(By.CSS_SELECTOR, "[aria-colindex='3']")
                skip = ["hypothetical", "putative"]
                if not any(pe in hhpredInfo.text for pe in ["PE=4", "PE=5"]):
                    if all(s not in hhpredInfo.text.lower() for s in skip):
                        hhpredResults.append({
                            "annotation": anno[n],
                            "hhpred": hhpredInfo.text
                        })
                        print([anno[n], hhpredInfo.text])
                        break
            time.sleep(2)
            driver.back()
            time.sleep(2)
            while driver.current_url != "https://toolkit.tuebingen.mpg.de/tools/hhpred":
                driver.back()
                time.sleep(2)
            n += 1
        print(hhpredResults)
    except KeyboardInterrupt:
        print("ended, saving...")
    finally:
        with open("C:/Users/zillr/OneDrive/Desktop/Genenotator/results.json", "w") as f:
            json.dump(hhpredResults, f, indent=4)
    driver.quit()
    return hhpredResults

data = getPhageAnnoGenes(findPhages(1, 5))
fastas = [item[0] for item in data]
annos = [item[1] for item in data]
print("-" * 100)
hhpred(fastas, annos)
