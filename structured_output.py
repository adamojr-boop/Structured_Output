import os, json
from textwrap import dedent
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv(Path.cwd() / ".env", override=True)

#Esempio 1#

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY non trovata nel file .env")

client = OpenAI(api_key=api_key)
MODEL = "gpt-4o"

#Math tutor#

math_tutor_prompt = """
Sei un tutor di matematica.
Ti verrà fornito un problema matematico,
e il tuo obiettivo sarà quello di fornire una soluzione
passo dopo passo, insieme a una risposta finale.
Per ogni passaggio, è sufficiente fornire l'output (output) come equazione
e utilizzare il campo della spiegazione (explanation) per dettagliare il ragionamento.
"""

def get_math_solution(question):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "developer",
                "content": math_tutor_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "explanation": {"type": "string"},
                                    "output": {"type": "string"}
                                },
                                "required": ["explanation", "output"],
                                "additionalProperties": False
                            }
                        },
                        "final_answer": {"type": "string"}
                    },
                    "required": ["steps", "final_answer"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    )
    return response.choices[0].message

question = "come posso risolvere 8 x + 7 = -23"

result = get_math_solution(question)

content = result.content

print(content)

obj = json.loads(content)

print("*" * 80)

steps = obj['steps']
final_answer = obj['final_answer']

for step in steps:
    explanation = step['explanation']
    output = step['output']
    print("explanation: ", explanation, "\n")
    print("output: ", output, "\n")

print("final_answer: ", final_answer, "\n")

#Esempio 2#

articles = [
    "./structured_outputs_articles/www.md",
    "./structured_outputs_articles/pic.md",
    "./structured_outputs_articles/magn.md"
]

def get_article_content(path):
    with open(path, 'r', encoding="utf8") as f:
        content = f.read()
        return content

content = [get_article_content(path) for path in articles]

class ArticleSummary(BaseModel):
    invented_year: int
    summary: str
    inventors: list[str]
    description: str

    class Concept(BaseModel):
        title: str
        description: str

    concepts: list[Concept]

    def __str__(self):
        inventors = "\n".join(f"- {i}" for i in self.inventors)
        concepts = "\n".join(f"- {c.title}: {c.description}" for c in self.concepts)
        
        return f"""
Invented year: {self.invented_year}

Summary: {self.summary}

Inventors:
{inventors}

Concepts:
{concepts}

Description: {self.description}
"""

summarization_prompt = """
Ti verrà fornito il contenuto di un articolo su un'invenzione.
Il tuo obiettivo sarà quello di riassumere l'articolo seguendo lo schema fornito.
Ecco una descrizione dei parametri:
- invented_year: anno in cui è stata inventata l'invenzione di cui si parla nell'articolo
- summary: riassunto in una frase che descrive l'invenzione
- inventors: array di stringhe che elencano i nomi completi degli inventori, se presenti, altrimenti solo il cognome
- concepts: array di concetti chiave relativi all'invenzione, ogni concetto contiene un titolo e una descrizione
- description: breve descrizione dell'invenzione
"""

def get_article_summary(text: str):
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": dedent(summarization_prompt)},
            {"role": "user", "content": text}
        ],
        response_format=ArticleSummary,
    )
    
    return completion.choices[0].message.parsed

summaries = []

for i in range(len(content)):
    print(f"Analyzing article #{i+1}...")
    summaries.append(get_article_summary(content[i]))
    print("Done.")

for i in range(len(summaries)):
    print(f"ARTICLE {i + 1}\n")
    print(summaries[i])
    print("\n\n")