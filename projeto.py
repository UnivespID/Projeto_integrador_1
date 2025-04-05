from flask import Flask, render_template, request, redirect, url_for 
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# Modelo de Item atualizado
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    lote = db.Column(db.String(50))  # Campo para lote
    data_entrada = db.Column(db.Date)  # Campo para data de entrada
    data_validade = db.Column(db.Date)  # Campo para data de validade

# Modelo de Movimentação atualizado
class Movimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item', backref=db.backref('movimentacoes', lazy=True))
    tipo = db.Column(db.String(10), nullable=False)  # 'Entrada' ou 'Saída'
    quantidade = db.Column(db.Integer, nullable=False)
    usuario = db.Column(db.String(100))  # Campo para usuário que removeu
    data = db.Column(db.DateTime, default=datetime.utcnow)

# Página principal com filtro de itens
@app.route('/')
def index():
    filtro = request.args.get('filtro')
    if filtro:
        itens = Item.query.filter(Item.nome.contains(filtro)).order_by(Item.data_validade).all()
    else:
        itens = Item.query.order_by(Item.data_validade).all()
    return render_template('index.html', itens=itens, filtro=filtro)

# Adicionar item ao estoque
@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])
    lote = request.form['lote']
    data_entrada = datetime.strptime(request.form['data_entrada'], '%Y-%m-%d').date()
    data_validade = datetime.strptime(request.form['data_validade'], '%Y-%m-%d').date()

    # Buscar item pelo nome, lote, data de entrada e validade
    item = Item.query.filter_by(nome=nome, lote=lote, data_entrada=data_entrada, data_validade=data_validade).first()

    # Se encontrar um item igual, apenas soma a quantidade
    if item:
        item.quantidade += quantidade
    else:
        # Se não, cria um novo registro
        item = Item(nome=nome, quantidade=quantidade, lote=lote, data_entrada=data_entrada, data_validade=data_validade)
        db.session.add(item)
        db.session.flush()  # Salva temporariamente para obter o ID

    movimentacao = Movimentacao(item_id=item.id, tipo='Entrada', quantidade=quantidade)
    db.session.add(movimentacao)
    db.session.commit()
    return redirect(url_for('index'))

# Remover item do estoque
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

# Página do histórico de movimentações
@app.route('/historico')
def historico():
    movimentacoes = Movimentacao.query.order_by(Movimentacao.data.desc()).all()
    return render_template('historico.html', movimentacoes=movimentacoes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)