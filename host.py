# Dependencies
import hashlib as hasher
import datetime as date
from collections import OrderedDict
from flask import Flask
from flask import request
from flask import jsonify
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto import Random
import binascii
node = Flask(__name__)

class Block:
    def __init__(self, i, timestamp, data, previousHash):
        self.i = i
        self.timestamp = timestamp
        self.data = data
        self.previousHash = previousHash
        self.hash = self.hashNewBlock()
    
    # Hash a new block to add to the chain
    def hashNewBlock(self):
        # Hash our block using Sha256
        sha = hasher.sha256()
        sha.update(str(self.i) + str(self.timestamp) + str(self.data) + str(self.previousHash))
        return sha.hexdigest()

# Methods for block handling
# Generate our first block - essential for the start of the chain
def genFirstBlock():
    # Create our first block for the chain using an arbitrary value and an index of 0
    return Block(0, date.datetime.now(), "GEN_BLOCK", "ARBITRARY")

# Create our new block using last block
def generateBlock(lastBlock, blockData):
    myIndex = lastBlock.i + 1
    myTimestamp = date.datetime.now()
    myData = blockData
    previousHash = lastBlock.hash
    return Block(myIndex, myTimestamp, myData, previousHash)

    # Coin interaction
def proveWork(lastProof):
    # Set the proof to be 1+ of the last proof so that we can make the computer do work.
    nextProof = lastProof + 1

    while (nextProof % 11 != 0 and nextProof % lastProof != 0):
        nextProof += 1

    # Return our proof of work done
    return nextProof


# Methods for blockchain access
# Store all the transactins for this node
transactions = []
blockchain = []
wallets = []

@node.route('/mine', methods = ['POST'])
def mine():
    minerAddress = request.form['minerAddress']

    if (len(blockchain) < 1):
        firstBlock = genFirstBlock()
        
        firstBlockData = {
            "proof": 1,
            "transactions": ''
        }
    
        newIndex = 0
        newTimestamp = date.datetime.now()
        lastHash = 'GEN_BLOCK'
        
        # Create the new block
        newBlock = Block(
            newIndex,
            newTimestamp,
            firstBlockData,
            lastHash
        )

        blockchain.append(newBlock)

    # Get what the last proof was
    lastBlock = blockchain[len(blockchain) - 1]
    lastProof = lastBlock.data['proof']
    
    # Do the next proof
    proof = proveWork(lastProof)
    
    # Once we have proved the work we can continue with the transaction and reward the client
    #transactions.append(
    #    { "from": "provider", "to": minerAddress, "amount": 1, "signature": 'unsigned' }
    #) No longer appending mining transactions to our transaction array
  
    # Create our new block
    blockData = {
        "proof": proof,
        "transactions": list(transactions)
    }
    
    newIndex = lastBlock.i + 1
    newTimestamp = date.datetime.now()
    lastHash = lastBlock.hash
    
    # Create the new block
    newBlock = Block(
        newIndex,
        newTimestamp,
        blockData,
        lastHash
    )

    blockchain.append(newBlock)

    # Let the client know that they successfully made the transaction
    return jsonify({
        "index": newIndex,
        "timestamp": str(newTimestamp),
        "data": blockData,
        "hash": lastHash
    }), 200


@node.route('/blocks', methods=['GET'])
def get_blocks():
  chain = blockchain

  # Convert our block to return as json
  for i in range(len(chain)):
    block = chain[i]
    blockIndex = str(block.i)
    blockTimestamp = str(block.timestamp)
    blockData = str(block.data)
    blockHash = block.hash
    chain[i] = {
      "index": blockIndex,
      "timestamp": blockTimestamp,
      "data": blockData,
      "hash": blockHash
    }
  chain = jsonify(chain)
  return chain

# Wallet Upkeep
@node.route('/new/wallet', methods=['POST'])
def newWallet():
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    tfn = request.form['tfn']
    address = request.form['address']

    randGen = Random.new().read
    privateKey = RSA.generate(1024, randGen)
    publicKey = privateKey.publickey()
    wallet = {
        'privateKey': binascii.hexlify(privateKey.exportKey(format='DER')).decode('ascii'),
        'publicKey': binascii.hexlify(publicKey.exportKey(format='DER')).decode('ascii'),
        'user': {
            "firstName": firstName,
            "lastName": lastName,
            "tfn": tfn,
            "address": address,
            "transactions": []
        }
    }

    # Add our wallet to our list of wallets
    wallets.append(wallet)
    return jsonify(wallet), 200

def signTransaction(privateKey, senderAddress, candidateAddress, transactionAmount):
    signer = PKCS1_v1_5.new(privateKey)
    sha = hasher.sha256()
    sha.update(str(senderAddress) + str(candidateAddress) + str(transactionAmount))
    return sha.hexdigest()

@node.route('/new/transaction', methods=['POST'])
def transaction():
    # Extract body from post
    senderAddress = request.form['senderAddress']
    senderPrivateKey = request.form['senderPrivateKey']
    candidateAddress = request.form['candidateAddress']
    transactionAmount = request.form['transactionAmount']

    # Get what the last proof was
    lastBlock = blockchain[len(blockchain) - 1]
    lastProof = lastBlock.data['proof']
    
    transactionModel = { "from": senderAddress, "to": candidateAddress, "amount": transactionAmount, 'signature': signTransaction(senderPrivateKey, senderAddress, candidateAddress, transactionAmount) }

    # Once we have proved the work we can continue with the transaction and reward the client
    transactions.append(transactionModel)

    for x in range(0, len(wallets)):
        if wallets[0]['publicKey']:
            wallets[0]['user']['transactions'].append(transactionModel)
  
    # Create our new block
    blockData = {
        "proof": lastProof,
        "transactions": list(transactions)
    }
    
    newIndex = lastBlock.i + 1
    newTimestamp = date.datetime.now()
    lastHash = lastBlock.hash
    
    # Create the new block
    newBlock = Block(
        newIndex,
        newTimestamp,
        blockData,
        lastHash
    )

    blockchain.append(newBlock)

    # Let the client know that they successfully made the transaction
    return jsonify({
        "index": newIndex,
        "timestamp": str(newTimestamp),
        "data": blockData,
        "hash": lastHash
    }), 200

@node.route('/transactions', methods=['GET'])
def getTransactions():
    # Return our transactions from our blockchain
    response = {'transactions': transactions}
    return jsonify(response), 200

@node.route('/wallets', methods=['GET'])
def getWallets():
    # Return our wallets
    response = {'wallets': wallets}
    return jsonify(response), 200

node.run()
