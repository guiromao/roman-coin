# -*- coding: utf-8 -*-
"""
Created on Sun May 30 13:06:17 2021

@author: Guilherme
"""
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#part 1, create Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'transactions': self.transactions,
                 'previous_hash': previous_hash}
        
        self.transactions = [] 
        self.chain.append(block)
        
        return block
    
    
    def get_previous_block(self):
        return self.chain[-1] #last block
    
    
    #mining
    def proof_of_work(self, previous_proof):
        new_proof = 1 #proof is like nonce
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            #new_proof **2 - previous_proof**2 is the difficult level
            if hash_operation[:4] == '0000': #if there's 4 zeros on the left
                check_proof = True
            else:
                new_proof += 1
                
        return new_proof
    
    
    #generating hash of block
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode() #generates json block, as String
        
        return hashlib.sha256(encoded_block).hexdigest()
    
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block.proof
            proof = block.proof
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2)).encode().hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
            
        return True
    
    
    #to add a transaction, and return the block where the transaction will be added to
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
                'sender': sender,
                'receiver': receiver,
                'amount': amount
            })
        
        previous_block = self.get_previous_block()
        
        return previous_block['index'] + 1
    
    
    #adding nodes
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url)
        
        
        
    #consensus method
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > longest_chain and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
           
        #if longest_chain has something, therefore there's a longer chain            
        if longest_chain: 
            self.chain = longest_chain
            return True
        
        return False
                    
    
    
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_address = str(uuid4()).replace("-", "")

blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, receiver='James Bond', amount=100)
    block = blockchain.create_block(proof, previous_hash)
    
    response = {
                'message': 'Congrats on mining a new block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'transactions': block['transactions'],
                'previous_hash': block['previous_hash']
                }
    
    return jsonify(response), 200


@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
                'chain': blockchain.chain,
                'length': len(blockchain.chain)
                }
    
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    response = {
            'isValid': blockchain.is_chain_valid(blockchain.chain)
        }
    
    return jsonify(response), 200


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amound']
    
    if not all(key in json for key in transaction_keys):
        return "Some elements are missing...", 400
    
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to the next block, number {index}'}
    
    return jsonify(response), 201


@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    
    if nodes is None:
        return "No nodes connected to this network...", 400
    
    for node in nodes:
        blockchain.add_node(node)
        
    response = {
        'message': 'These are the connected nodes to the blockchain!',
        'total_nodes': list(blockchain.nodes)
    }
    
    return jsonify(response), 201


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    response = ''
    
    if is_chain_replaced:
        response = {
            'message': 'Blockchain was updated in the node!',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': "Blockchain wasn't updated in the node.",
            'same_chain': blockchain.chain
        }
        
    return jsonify(response), 201
    

app.run(host='0.0.0.0', port=5002)

#yeahhh Roman Coins!!!!BLINGBLINGBLING!!!!
