pragma solidity ^0.5.0;

contract Types {

   uint[6] data;  
  
    function array_example() public returns (uint[6] memory){
          
        data = [uint(10), 20, 30, 40, 50, 60];
        
        return (data);
    }
}
