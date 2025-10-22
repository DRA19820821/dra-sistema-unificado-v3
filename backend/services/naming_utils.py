import re
from unidecode import unidecode

def gerar_id_topico(radical: str, indice: int, topico: str) -> str:
    """Gera ID único do tópico."""
    numero = str(indice + 1).zfill(2)
    abreviacao = abreviar_topico(topico)
    return f"{radical}{numero}_{abreviacao}"

def gerar_nome_arquivo(radical: str, indice: int, topico: str) -> str:
    """Gera nome do arquivo HTML."""
    return f"{gerar_id_topico(radical, indice, topico)}.html"

def abreviar_topico(topico: str, max_chars: int = 40) -> str:
    """Abrevia tópico."""
    texto = unidecode(topico)
    texto = re.sub(r'[^\w\s-]', '', texto)
    palavras = texto.split()
    
    abreviacoes = []
    for palavra in palavras:
        abrev = palavra[:3].capitalize()
        abreviacoes.append(abrev)
    
    resultado = ''.join(abreviacoes)
    return resultado[:max_chars]
