import requests
import json
import itertools
import threading
import time
from colorama import Fore, Style, init

init(autoreset=True)
BASEURL = 'http://127.0.0.1:5000'

# Función para generar el prompt
def generate_prompt(main_name, secondary_name, place, event, tokens):
  prompt = (
          f"Escribe una historia donde el personaje principal se llama {main_name}, "
          f"el personaje secundario se llama {secondary_name}, la historia ocurre en {place}, "
          f"y una acción importante que debe acontecer es {event}."
          f"La historia no debe tener más de {tokens} tokens."
        )
  return prompt

# Función para obtener la historia desde la API
def get_history(prompt, model, tokens, creativity):
    global done
    url = f"{BASEURL}/v1/completions"
    headers = {'Content-Type': 'application/json'}
    
    creativity = creativity / 100  # Convertir la creatividad a un valor entre 0 y 1
    
    payload = {'prompt': prompt, 'max_tokens': tokens, 'model': model, 'temperature': creativity}
    
    done = False
    t = threading.Thread(target=spinner, args=("Generando historia",))
    t.start()
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP 4xx/5xx
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error en la solicitud: {e}{Style.RESET_ALL}")
        return None
    finally:
        done = True
        t.join()
    
    try:
        data = response.json()
        return data['choices'][0]['text']  # Devuelve el texto generado por la IA
    except (json.JSONDecodeError, KeyError) as e:
        print(f"{Fore.RED}Error al decodificar la respuesta JSON: {e}{Style.RESET_ALL}")
        return None

# Función para solicitar datos al usuario
def get_user_input():
  print(f"{Fore.CYAN}\nPor favor, introduce los siguientes datos para generar la historia (o escribe 'quit' para salir):{Style.RESET_ALL}")
  main_name = input(f"{Fore.YELLOW}Nombre del personaje principal: {Style.RESET_ALL}")
  if main_name.lower() == 'quit':
    return None, None, None, None, None, None
  secondary_name = input(f"{Fore.YELLOW}Nombre del personaje secundario: {Style.RESET_ALL}")
  if secondary_name.lower() == 'quit':
    return None, None, None, None, None, None
  place = input(f"{Fore.YELLOW}Lugar donde ocurre el relato: {Style.RESET_ALL}")
  if place.lower() == 'quit':
    return None, None, None, None, None, None
  event = input(f"{Fore.YELLOW}Acción importante que debe acontecer en la historia: {Style.RESET_ALL}")
  if event.lower() == 'quit':
    return None, None, None, None, None, None
  tokens = int(input(f"{Fore.YELLOW}Número de tokens para generar la historia (dependiendo del modelo que elijas, más de 200 tokens pueden generar tiempos largos de procesamiento): {Style.RESET_ALL}"))
  if main_name.lower() == 'quit':
    return None, None, None, None, None, None
  creativity = int(input(f"{Fore.YELLOW}Creatividad (0-100): {Style.RESET_ALL}"))
  if main_name.lower() == 'quit':
    return None, None, None, None, None, None
  return main_name, secondary_name, place, event, tokens, creativity

# Función para seleccionar el modelo
def select_model(models):
  print(f"{Fore.CYAN}\nSelecciona un modelo para generar la historia:{Style.RESET_ALL}")
  for i, model in enumerate(models, 1):
    print(f"{Fore.YELLOW}{i}. {model}{Style.RESET_ALL}")
  model_choice = int(input(f"{Fore.YELLOW}Introduce el número del modelo: {Style.RESET_ALL}")) - 1
  load_model(models[model_choice])
  
  return models[model_choice]

# Función para mostrar el menú de opciones
def show_menu():
  print(f"{Fore.CYAN}\n¿Qué te gustaría hacer a continuación?{Style.RESET_ALL}")
  print(f"1. Regenerar historia")
  print(f"2. Cambiar modelo")
  print(f"3. Cambiar creatividad")
  print(f"4. Crear nueva historia")
  print(f"0. Salir{Style.RESET_ALL}")
  return input(f"{Fore.YELLOW}Introduce el número de la opción: {Style.RESET_ALL}")

def get_models():
  url = f"{BASEURL}/v1/internal/model/list"
  try:
      response = requests.get(url)
      response.raise_for_status()
      data = response.json()
      models = data['model_names']
      return models
  except requests.exceptions.RequestException as e:
      print(f"{Fore.RED}Error al obtener la lista de modelos: {e}{Style.RESET_ALL}")
      return []

def spinner(message):
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        print(f'\r{Fore.YELLOW}{message} {c}', end='', flush=True)
        time.sleep(0.1)
    print('\r', end='', flush=True)

def load_model(model):
    global done
    url = f"{BASEURL}/v1/internal/model/load"
    
    body = {
        'model_name': model,
        "args": {
            "load_in_4bit": True,
            "n_gpu_layers": 12,
        },
        "settings": {
            "instruction_template": "Alpaca"
        }
    }
    
    done = False
    t = threading.Thread(target=spinner, args=("Cargando modelo",))
    t.start()
    
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(body))
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP 4xx/5xx
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error en la solicitud: {e}{Style.RESET_ALL}")
    finally:
        done = True
        t.join()
    
    return response

# Función principal
def main():
  models = get_models()
  if not models:
      print(f"{Fore.RED}No se pudieron obtener los modelos. Saliendo...{Style.RESET_ALL}")
      return

  first_run = True
  main_name = secondary_name = place = event = selected_model = None

  while True:
    if first_run:
      main_name, secondary_name, place, event, tokens, creativity = get_user_input()
      if main_name is None:
        break
      selected_model = select_model(models)
      first_run = False
    else:
      option = show_menu()
      if option == '1':
        pass  # Regenerar historia con los mismos datos y modelo
      elif option == '2':
        selected_model = select_model(models)
      elif option == '3':
        creativity = int(input(f"{Fore.YELLOW}Creatividad (0-100): {Style.RESET_ALL}"))
      elif option == '4':
        first_run = True
        continue
      elif option == '0':
        break
      else:
        print(f"{Fore.RED}Opción no válida. Por favor, intenta de nuevo.{Style.RESET_ALL}")
        continue

    # Generar el prompt y obtener la historia
    prompt = generate_prompt(main_name, secondary_name, place, event, tokens)
    print(f"\n{Fore.MAGENTA}Generando la historia con el modelo {selected_model}...{Style.RESET_ALL}")
    history = get_history(prompt, selected_model, tokens, creativity)

    # Mostrar la historia generada
    print(f"\n{Fore.GREEN}Historia generada:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{history}{Style.RESET_ALL}")

if __name__ == "__main__":
  main()