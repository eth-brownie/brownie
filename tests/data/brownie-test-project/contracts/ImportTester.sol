// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import {ERC721PresetMinterPauserAutoId} from "@openzeppelin/contracts/token/ERC721/presets/ERC721PresetMinterPauserAutoId.sol";

contract ImportTester is
    ERC721PresetMinterPauserAutoId("Name", "Symbol", "BaseURI")
{}
