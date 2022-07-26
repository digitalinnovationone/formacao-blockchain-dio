pragma solidity ^0.5.0;

contract Types {
  
  int[] data;
  
  function dynamic_array() public returns(int[] memory){
  
    data = [int(-60), 70, -80, 90, -100, -120, 140];
    data.push(200);
    return (data);
  }
}
