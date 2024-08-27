//importando as dependencias
//bip32 - significa bitcoin improvement proposal número 32, 39, etc
const bip32 = require('bip32')
const bip39 = require('bip39')
const bitcoin = require('bitcoinjs-lib')

//definir a rede
//bitcoin - rede principal - mainnet
//testnet - rede de teste - testnet
const network = bitcoin.networks.testnet

//derivação de carteiras HD (Hierarquica ou Deterministica)
const path = "m/49'/1'/0'/0"

//criando o mnemonic para a seed (palavras de senha)
let mnemonic = bip39.generateMnemonic()
const seed = bip39.mnemonicToSeedSync()

//criando a raiz da carteira HD
let root = bip32.fromSeed(seed, network)

//criando uma conta - par pvt-pub keys
let account = root.derivePath(path)
let node = account.derive(0).derive(0)

let btcAddress = bitcoin.payments.p2wpkh({

    pubkey: node.publicKey,

    network: network,

}).address

console.log("Carteira gerada")
console.log("Endereço: ", btcAddress)
console.log("Chave privada:", node.toWIF())
console.log("Seed", mnemonic)

//após gerar a chave privada, é preciso importar a chave gerada para dentro de um sofware regenciador de carteiras