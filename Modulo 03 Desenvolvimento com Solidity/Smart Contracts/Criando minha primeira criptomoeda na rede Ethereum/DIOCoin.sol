// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8; //compilador

interface IERC20 { //criando interface no padrão IERC20

    //CRIANDO MÉTODOS/FUNÇÕES

    //suprimento total de tokens no meu contato
    function totalSupply() external view returns (uint256);

    //checa o saldo de um endereço específico
    function balanceOf(address account) external view returns (uint256);

    //limite de saldo disponibilizado para que outro endereço(usuário) possa usar (como se fosse uma procuração para alguem sacar da minha conta bancária)
    function allowance(address owner, address spender) external view returns (uint256);

    //tranferencia de tokens
    function transfer(address recipient, uint256 amount) external returns (bool);

    //aprovando uma transação de alguém que recebeu permissão de gastar o saldo que disponibilizei
    function approve(address spender, uint256 amount) external returns (bool);

    //informando o que estou gastanto do allowance disponibilizado
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

    //EVENTOS DISPARADOS 
    event Transfer(address indexed from, address indexed to, uint256 value);
    
    event Approval(address indexed owner, address indexed spender, uint256);

}

contract DioCoin is IERC20{

    string public constant name = "DIO Coin";
    string public constant symbol = "DIO";
    uint8 public constant decimals = 18;

    mapping  (address => uint256) balances;
    mapping (address =>mapping (address=>uint256)) allowed;

    uint256 totalSupply_ = 10 ether;

    constructor(){
        balances[msg.sender] = totalSupply_;
    }

    function totalSupply() public override view returns (uint256){
        return totalSupply_;
    }

    function balanceOf(address tokenOwner) public override view returns(uint256){
        return balances[tokenOwner];
    }


    function transfer(address receiver, uint256 numTokens) public override returns (bool) {
        require(numTokens <= balances[msg.sender]); //exige que a quantidade do salddo que esta enviando
        balances[msg.sender] = balances[msg.sender]-numTokens; //o emitente decrementa o valor do saldo
        balances[receiver] = balances[receiver]+numTokens; //o recebedor incrementa o valor no saldo
        emit Transfer(msg.sender, receiver, numTokens); //dispara um evento dos enderecos e a quantidade
        return true; 
    }

    function approve(address delegate, uint256 numTokens) public override returns (bool){
        allowed[msg.sender][delegate] = numTokens;
        emit Approval(msg.sender, delegate, numTokens);
        return true;
    }

    function allowance(address owner, address delegate) public override view returns (uint){
        return allowed[owner][delegate];
    }

    function transferFrom(address owner, address buyer, uint256 numTokens) public override returns (bool){
        require(numTokens <= balances[owner]);
        require(numTokens <= allowed[owner][msg.sender]);

        balances[owner] = balances[owner]-numTokens;
        allowed[owner][msg.sender] = allowed[owner][msg.sender]-numTokens;
        balances[buyer] = balances[buyer]+numTokens;
        emit Transfer(owner, buyer, numTokens);
        return true;
    }

}