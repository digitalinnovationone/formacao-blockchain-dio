* Sergioaero1 - Ótimo repositório 

Entendi bem as partes importantes. na rática tive dificuldades. Pesquisei para encontrar os erros. Consegui um fork de um código funcionando. ele esta um pouco dierente do código desse curso, normal, as coisas atualizaram e oi bom para mim buscar atualização e ver o código funcionando. 

Meu código estava dando erro na linha que deveria gerar o endereço da carteira.   

* SEGUE O CÓDIGO QUE RESOLVEU MEU PROBLEMA 2024:

// Importing dependencies

const bip32 = require('bip32');

const bip39 = require('bip39');

const bitcoin = require('bitcoinjs-lib');



// Define network parameters for Testnet4

const testnet4 = {

  messagePrefix: '\x18Bitcoin Signed Message:\n',

  bech32: 'tb',

  bip32: {

    public: 0x043587cf,  // Base58 prefix for xpub on Testnet4

    private: 0x04358394  // Base58 prefix for xprv on Testnet4

  },

  pubKeyHash: 0x6f,      // P2PKH starts with 'm' or 'n'

  scriptHash: 0xc4,      // P2SH starts with '2'

  wif: 0xef              // Wallet Import Format prefix

};



// HD wallets derivation path for Testnet4

const path = `m/49'/1'/0'/0`;



// Generating mnemonic (seed phrase)

let mnemonic = bip39.generateMnemonic();

const seed = bip39.mnemonicToSeedSync(mnemonic);



// Creating HD wallet root from the seed

let root = bip32.fromSeed(seed, testnet4);



// Deriving account and generating address

let account = root.derivePath(path);

let node = account.derive(0).derive(0);



let btcAddress = bitcoin.payments.p2pkh({

  pubkey: node.publicKey,

  network: testnet4,

}).address;



console.log("Carteira Criada por Testnet4");

console.log("Address: ", btcAddress);

console.log("Private Key: ", node.toWIF());

console.log("Seed Phrase: ", mnemonic);


