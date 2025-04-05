from flask import Flask, render_template, request, redirect, url_for 
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Criar app e configurar
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================
# MODELOS
# =========================

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    lote = db.Column(db.String(50))
    data_entrada = db.Column(db.Date)
    data_validade = db.Column(db.Date)

class Movimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item', backref=db.backref('movimentacoes', lazy=True))
    tipo = db.Column(db.String(10), nullable=False)  # 'Entrada' ou 'Saída'
    quantidade = db.Column(db.Integer, nullable=False)
    usuario = db.Column(db.String(100))
    data = db.Column(db.DateTime, default=datetime.utcnow)

# =========================
# ROTAS
# =========================

@app.route('/')
def index():
    filtro = request.args.get('filtro')
    if filtro:
        itens = Item.query.filter(Item.nome.contains(filtro)).order_by(Item.data_validade).all()
    else:
        itens = Item.query.order_by(Item.data_validade).all()
    return render_template('index.html', itens=itens, filtro=filtro)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])
    lote = request.form['lote']
    data_entrada = datetime.strptime(request.form['data_entrada'], '%Y-%m-%d').date()
    data_validade = datetime.strptime(request.form['data_validade'], '%Y-%m-%d').date()

    item = Item.query.filter_by(nome=nome, lote=lote, data_entrada=data_entrada, data_validade=data_validade).first()
    if item:
        item.quantidade += quantidade
    else:
        item = Item(nome=nome, quantidade=quantidade, lote=lote, data_entrada=data_entrada, data_validade=data_validade)
        db.session.add(item)
        db.session.flush()

    movimentacao = Movimentacao(item_id=item.id, tipo='Entrada', quantidade=quantidade)
    db.session.add(movimentacao)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/remover', methods=['POST'])
def remover():
    id_item = int(request.form['id'])
    quantidade = int(request.form['quantidade'])
    usuario = request.form['usuario']

    item = Item.query.get(id_item)
    if item and item.quantidade >= quantidade:
        item.quantidade -= quantidade
        movimentacao = Movimentacao(item_id=item.id, tipo='Saída', quantidade=quantidade, usuario=usuario)
        db.session.add(movimentacao)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/historico')
def historico():
    movimentacoes = Movimentacao.query.order_by(Movimentacao.data.desc()).all()
    return render_template('historico.html', movimentacoes=movimentacoes)

# Rota para forçar a criação do banco
@app.route('/initdb')
def initdb():
    try:
        db.create_all()
        return 'Banco de dados criado com sucesso!'
    except Exception as e:
        return f'Erro ao criar banco: {str(e)}'

# =========================
# EXECUTAR LOCAL
# =========================

if __name__ == '__main__':
    app.run(debug=True)
