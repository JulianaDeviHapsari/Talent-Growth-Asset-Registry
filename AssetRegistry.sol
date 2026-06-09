pragma solidity ^0.8.20;

contract AssetRegistry {

    struct Asset {
        string  assetId;
        address owner;
        string  assetType;
        bytes32 metadataHash;
        uint256 registeredAt;
        bool    exists;
    }

    mapping(string => Asset) private _assets;
    mapping(address => string[]) private _ownerAssets;

    event AssetRegistered(
        string  indexed assetId,
        address indexed owner,
        string          assetType,
        bytes32         metadataHash,
        uint256         timestamp
    );

    error AssetAlreadyExists(string assetId);
    error AssetNotFound(string assetId);

    function registerAsset(
        string  calldata assetId,
        string  calldata assetType,
        bytes32          metadataHash
    ) external {
        if (_assets[assetId].exists) revert AssetAlreadyExists(assetId);

        _assets[assetId] = Asset({
            assetId:      assetId,
            owner:        msg.sender,
            assetType:    assetType,
            metadataHash: metadataHash,
            registeredAt: block.timestamp,
            exists:       true
        });

        _ownerAssets[msg.sender].push(assetId);
        emit AssetRegistered(assetId, msg.sender, assetType, metadataHash, block.timestamp);
    }

    function getAsset(string calldata assetId)
        external view
        returns (address owner, string memory assetType, bytes32 metadataHash, uint256 registeredAt)
    {
        Asset storage asset = _assets[assetId];
        if (!asset.exists) revert AssetNotFound(assetId);
        return (asset.owner, asset.assetType, asset.metadataHash, asset.registeredAt);
    }

    function getOwnerAssets(address owner) external view returns (string[] memory) {
        return _ownerAssets[owner];
    }
}