# CONSTANTS:
ALLOWED_STATUS = {
    "Reading",
    "Read",
    "Unread"
}

ALLOWED_GENRES = {
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Thriller",
    "Romance",
    "Horror",
    "Historical Fiction",
    "Biography",
    "Non-fiction",
}

ALLOWED_BOOK_FIELDS = {
    "title",
    "author",
    "genre",
    "year",
    "description",
    "rating",
    "status"
}

# VALIDADE USER FUNCTION: essas funções são validações de entrada -> do que o cliente envia.
def validate_user_data(user):
    for field in ["name","email","password"]: # essa validação parece redundante mas não é: se alguém enviar besteira, a coisa nem chega no banco. Este nem as recebe.
        if not isinstance(user[field], str) or not user[field].strip(): # esse último or impede strings vazias ou só com espaços.
            return False

    if len(user["name"]) > 50: # Se o nome tiver mais de 50 caracteres -> inválido.
        return False

    if user["email"].count("@") != 1: # "Se o email não tiver exatamente um @, é inválido."
        return False

    if user["email"].find("@") == 0: # Se não houver caracteres antes do @, rejeita"
        return False

    if user["email"].find("@") > user["email"].find("."): # user["email"].find("@") devolver a posição onde @ aparece
        return False # "Se o @ aparecer depois do primeiro ponto, rejeita."

    if user["email"].find(".") >= len(user["email"]) -1:
        return False # Se o primeiro ponto. estiver no último índice (ou além dele), rejeita.

    if len(user["password"]) < 8: # Se a senha não tiver pelo menos 8 caracteres → inválida
        return False

    return True

# FUNCTION TO VALIDATE BOOK DATA:
# Regras de validação para os campos do Book: ela não foi feita para validar um género isolado. Ela foi feita para validar um dicionário de dados de Book.
def validate_book_data(data):
    # Validação dos campos básicos, caso tenham sido enviados:
    for field in ["title", "author", "genre"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return False
    if "genre" in data:
        if data["genre"] not in ALLOWED_GENRES:
            return False

    # Demais campos, verificação: foram enviados? Se sim -> São válidos?
    if "year" in data:
        if not isinstance(data["year"], int) or data["year"] < 0:
            return False

    if "description" in data: # se isso for enviado, o campo tem que ter algum conteúdo, não pode ser uma string vazia.
        if not isinstance(data["description"], str) or not data["description"].strip():
            return False

    if "rating" in data:
        if not isinstance(data["rating"], int):
            return False
        if not 0 <= data["rating"] <= 5:
            return False

    if "status" in data:
        if not isinstance(data["status"], str):
            return False
        if data["status"] not in ALLOWED_STATUS:
            return False

    return True
