import json
import random

from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configuração do Swagger
app.config['SWAGGER'] = {
    'title': 'GenRand - Sorteio de Números Aleatórios',
    'subtitle': 'Rotas',
    'description':
        'Esta é uma aplicação que permite gerar números aleatórios.',
    'version': '2.0',
    'securityDefinitions': {
        "bearerAuth": {
            "type": "apiKey",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "name": "Authorization",
            "in": "header",
        }
    },
    "security": [{"bearerAuth": []}]
}

app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
swagger = Swagger(app)
jwt = JWTManager(app)


# Modelo para armazenar os usuários
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password


# Classe para gerar os Números Randômicos
class RandomNumberService:

    def generate_random_number(self):
        min_value = random.randint(1, 100)
        max_value = random.randint(min_value + 1, 1000)
        quantity = random.randint(1, max_value - min_value + 1)
        available_numbers = list(range(min_value, max_value + 1))
        random.shuffle(available_numbers)
        random_numbers = sorted(available_numbers[:quantity])

        return {
            "min_value": min_value,
            "max_value": max_value,
            "quantity": quantity,
            "random_numbers": random_numbers
        }


# Documentação Swagger - Gerar os Números Randômicos
@app.route('/genrand', methods=['GET'])
@jwt_required()
def generate_random_number():
    """
  Rota para obter as numerações aleatórias.
  Lembre-se:

  - A quantidade de números que serão sorteados é gerada automaticamente.
  - O intervalo mínimo é gerado de modo aleatório.
  - O intervalo máximo é gerado de modo aleatório.
  ---
  security:
  - bearerAuth: []
  responses:
    200:
      description: Sucesso - Números gerados com sucesso
      schema:
        properties:
          max_value:
            type: integer
          min_value:
            type: integer
          quantity:
            type: integer
          random_numbers:
            type: integer
    403:
      description: Proibido - Acesso não autorizado
      schema:
        properties:
          message:
            type: string
  """
    random_service = RandomNumberService()
    random_number = random_service.generate_random_number()
    return jsonify(random_number)


# Rota para Registrar-se e coletar o token
@app.route('/register', methods=['POST'])
def register():
    """
  Rota para registrar e obter um Token.
  ---
  parameters:
  - name: user_data
    in: body
    required: true
    schema:
      type: object
      properties:
        username:
          type: string
        password:
          type: string
    description: Dados do usuário (JSON)
  responses:
    201:
      description: Registro efetuado com sucesso
      schema:
        properties:
          access_token:
            type: string
    400:
      description: Requisição inválida
      schema:
        properties:
          message:
            type: string
    409:
      description: Nome de usuário já está em uso
      schema:
        properties:
          message:
            type: string
  """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(
            {'message': 'Forneça um nome de usuário e uma senha válidos'}), 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({'message': 'Nome de usuário já está em uso'}), 409

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=username)

    return jsonify({
        'message': 'Registro bem-sucedido',
        'access_token': access_token
    }), 201


# Rota para Login e Renovar o token
@app.route('/login', methods=['POST'])
def login():
    """
  Rota para realizar o Login na Aplicação e obter um novo Token.
  ---
  parameters:
  - name: credentials
    in: body
    required: true
    schema:
      type: object
      properties:
        username:
          type: string
        password:
          type: string
    description: Dados do usuário (JSON)
  responses:
    200:
      description: Login bem-sucedido
      schema:
        properties:
          access_token:
            type: string
    400:
      description: Credenciais inválidas
      schema:
        properties:
          message:
            type: string
    403:
      description: Proibido - Acesso não autorizado
      schema:
        properties:
          message:
            type: string
  """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(
            {'message': 'Forneça um nome de usuário e uma senha válidos'}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404

    if not password == user.password:
        return jsonify({'message': 'Credenciais inválidas'}), 401

    access_token = create_access_token(identity=username)

    return jsonify({
        'message': 'Login bem-sucedido',
        'access_token': access_token
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=80, debug=True)
