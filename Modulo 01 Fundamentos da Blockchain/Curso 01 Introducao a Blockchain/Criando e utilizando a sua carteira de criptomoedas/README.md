# Validate version of Testnet you've used to create Wallet.

The code provided by the instructor generated a Wallet compatible with Testnet version 3. That leads to problems while verifying the creation of the wallet for some blockchain validators.

I could validate my wallet using https://blockstream.info/testnet and get a faucet using https://coinfaucet.eu/en/btc-testnet/

I've also researched how to generate the code to create wallets for Testnet version 4, as Testnet 3 should be "deprecated" soon, as shown below:

'''
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

        console.log("Generated Wallet for Testnet4");
        console.log("Address: ", btcAddress);
        console.log("Private Key: ", node.toWIF());
        console.log("Seed Phrase: ", mnemonic);
'''

