pragma solidity >=0.4.22 <0.6.0;

contract ScData {
    enum RequestType {PRODUCE,PRODUCEUPDATE,TRADE,TRACEADD,TRACEUPDATE,TRACKADD,TRACKUPDATE,INVALID}

    struct Fingerprint {
        bool setApi;
        bool setClient;
        uint fpVersion;
        bytes28 fpClient;
        bytes28 fpApi;
        uint apiTime;
        uint clientTime;
        RequestType clientRType;
        RequestType apiRType;
    }

    struct VersionedFingerprint {
        uint maxVersion;
        mapping (uint => Fingerprint) versions;
    }

    struct Fingerprints {
        bytes12  dataId;         // The Data Record ID
        uint clientCount;
        address[] clientAddresses;
        mapping (address => VersionedFingerprint) clientFingerprints; // Mapped by Client Addresses, the different Versions the Client submitted (or should submit) Fingerprints
    }

    //// Variables
    // The address of the Contract Manager
    address public managerAddress;
    // The address of the API
    address public apiAddress;
    // Fingerprint mappings. For a single dataId, there can be several fingerprints
    mapping (bytes12 => Fingerprints) fingerprints;
    mapping (address => bool) registered;

    //// Events
    event FingerprintAdded(bytes12 _dataId, uint _fpVersion, address _client, bool byApi);
    event FingerprintConfirmed(bytes12 _dataId, uint _fpVersion, address _client);
    event FingerprintMismatch(bytes12 _dataId, uint _fpVersion, address _client);
    // Can be raised by the API when a Client inserts an invalid version
    event InvalidVersion(bytes12 _dataId, uint _fpVersion, address _client);

    //// Modifiers
    modifier onlyClient() {
        require(msg.sender != apiAddress);
        require(registered[msg.sender] == true);
        _;
    }

    modifier onlyApi() {
        require(msg.sender == apiAddress);
        _;
    }

    modifier onlyManager() {
        require(msg.sender == managerAddress);
        _;
    }

    //// Constructor
    constructor() public {
        managerAddress = msg.sender;
    }

    //// Functions (Manager)
    function setApi(address _addr) public onlyManager {
        apiAddress = _addr;
    }

    function registerClient(address _caddr) public onlyManager {
        registered[_caddr] = true;
    }

    function removeClient(address _caddr) public onlyManager {
        registered[_caddr] = false;
    }

    //// Functions (TX)
    /**
     * Adds a Fingerprint Claim by API
     * @param _dataId The ID of the dataset
     * @param _fpVersion The Version of the dataset
     * @param _client the expected Client address
     * @param _rt The request Type the fingerprint belongs to. Should be included in the fingerprint nonetheless
     * @param _fp The Fingerprint of the dataset
     */
    function addFingerprintApi(bytes12 _dataId, uint _fpVersion, address _client, RequestType _rt, bytes28 _fp) public onlyApi {
        if (fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setApi) revert();

        if (_fpVersion > fingerprints[_dataId].clientFingerprints[_client].maxVersion) {
            fingerprints[_dataId].clientFingerprints[_client].maxVersion = _fpVersion;
        }

        insertClient(_dataId, _client);

        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setApi = true;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpVersion = _fpVersion;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpApi = _fp;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].apiRType = _rt;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].apiTime = getCurrentTime();

        validateFingerprint(_dataId, _fpVersion, _client, true);
    }

    function addFingerprintsApi(bytes12[] memory _dataId, uint[] memory _fpVersion, address[] memory _client, RequestType[] memory _rt, bytes28[] memory _fp) public onlyApi {
        uint l = _dataId.length;
        if (_fpVersion.length != l || _client.length != l || _rt.length != l || _fp.length != l) revert();

        for (uint i=0; i<l; i++) {
            addFingerprintApi(_dataId[i], _fpVersion[i], _client[i], _rt[i], _fp[i]);
        }
    }

    /**
     * Adds a Fingerprint Claim by a Client
     * @param _dataId The ID of the dataset
     * @param _fpVersion The Version of the dataset
     * @param _rt The request Type the fingerprint belongs to. Should be included in the fingerprint nonetheless
     * @param _fp The Fingerprint of the dataset
     */
    function addFingerprintClient(bytes12 _dataId, uint _fpVersion, RequestType _rt, bytes28 _fp) public onlyClient {
        address _client = msg.sender;

        if (fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setClient) revert();

        insertClient(_dataId, _client);

        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setClient = true;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpVersion = _fpVersion;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpClient = _fp;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].clientRType = _rt;
        fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].clientTime = getCurrentTime();

        validateFingerprint(_dataId, _fpVersion, _client, false);
    }

    function validateFingerprint(bytes12 _dataId, uint _fpVersion, address _client, bool byApi) private {
        emit FingerprintAdded(_dataId, _fpVersion, _client, byApi);

        if (fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setClient) {
            if (fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].setApi) {
                bytes28 fpc = fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpClient;
                bytes28 fpa = fingerprints[_dataId].clientFingerprints[_client].versions[_fpVersion].fpApi;
                if (fpCompare(fpc, fpa)) {
                    emit FingerprintConfirmed(_dataId, _fpVersion, _client);
                } else {
                    emit FingerprintMismatch(_dataId, _fpVersion, _client);
                }
            }
        }
    }

    function insertClient(bytes12 _dataId, address _client) private {
        if (!addressInArray(fingerprints[_dataId].clientAddresses, _client)) {
            fingerprints[_dataId].clientAddresses.push(_client);
        }
    }


    // Functions (Read)
    /**
     * Returns the number of clients that have or should have provided fingerprints for the given dataset
     * @param _dataId The ID of the dataset to check agains
     * @return The number of potential clients
     */
    function dataClientCount(bytes12 _dataId) public view returns (uint) {
        return fingerprints[_dataId].clientAddresses.length;
    }


    /**
     * Returns the highest version the API has provided a Fingerprint for.
     * This does explicitly not cover versions that only a client has provided a Fingerprint for!
     * If the returned version is 0, then no Fingerprint has been provided yet.
     * @param _dataId The ID of the dataset to check agains
     * @return The highest version the API has provided a Fingerprint for.
     */
    function dataVersionCount(bytes12 _dataId) public view returns (uint) {
        uint version = 0;

        for (uint i = 0; i < fingerprints[_dataId].clientAddresses.length; ++i) {
            address addr = fingerprints[_dataId].clientAddresses[i];
            version = max(version, fingerprints[_dataId].clientFingerprints[addr].maxVersion);
        }

        return version;
    }

    /**
     * Returns the number of provided fingerprints by different clients for a given version.
     * Even though clients can submit fingerprints for whatever dataset and version they want,
     * the API should provide a single fingerprint at maximum. This is, however, not enforced by the Smart Contract.
     */
    function dataVersionDuplicateCountClients(bytes12 _dataId, uint _version) public view returns (uint) {
        uint c = 0;

        for (uint i = 0; i < fingerprints[_dataId].clientAddresses.length; ++i) {
            address addr = fingerprints[_dataId].clientAddresses[i];
            if (fingerprints[_dataId].clientFingerprints[addr].versions[_version].setClient) {
                c++;
            }
        }

        return c;
    }

    /**
     * Returns the number of provided fingerprints by the API for a given version.
     * Even though clients can submit fingerprints for whatever dataset and version they want,
     * the API should provide a single fingerprint at maximum. If a value greater than 1 is returned, this indicates
     * a misbehaviour of the API.
     */
    function dataVersionDuplicateCountApi(bytes12 _dataId, uint _version) public view returns (uint) {
        uint c = 0;

        for (uint i = 0; i < fingerprints[_dataId].clientAddresses.length; ++i) {
            address addr = fingerprints[_dataId].clientAddresses[i];
            if (fingerprints[_dataId].clientFingerprints[addr].versions[_version].setApi) {
                c++;
            }
        }

        return c;
    }

    /**
     * Returns the address of the associated client for a dataset and version identified by an index.
     * The index corresponds to the duplicate count from `dataVersionDuplicateCountClients`.
     * Indexing starts at 0.
     * @return The address of the client or 0x0, if no client could be found.
    **/
    function getFingerprintByIndexClient(bytes12 _dataId, uint _version, uint _index) public view returns (address) {
        uint c = 0;

        for (uint i = 0; i < fingerprints[_dataId].clientAddresses.length; ++i) {
            address addr = fingerprints[_dataId].clientAddresses[i];
            if (fingerprints[_dataId].clientFingerprints[addr].versions[_version].setClient) {
                if (_index == i) {
                    return addr;
                }
                c++;
            }
        }

        return address(0x0);
    }

    /**
     * Returns the address of the associated client for a dataset and version identified by an index.
     * The index corresponds to the duplicate count from `dataVersionDuplicateCountApi`.
     * Indexing starts at 0.
     * @return The address of the client or 0x0, if no client could be found.
    **/
    function getFingerprintByIndexApi(bytes12 _dataId, uint _version, uint _index) public view returns (address) {
        uint c = 0;

        for (uint i = 0; i < fingerprints[_dataId].clientAddresses.length; ++i) {
            address addr = fingerprints[_dataId].clientAddresses[i];
            if (fingerprints[_dataId].clientFingerprints[addr].versions[_version].setApi) {
                if (_index == i) {
                    return addr;
                }
                c++;
            }
        }

        return address(0x0);
    }

    /**
     * Returns the members of the Fingerprint for a given version of a dataset issued by the given client address.
     * It further returns if the fingerprints of API and Client match.
     */
    function getFingerprint(bytes12 _dataId, uint _version, address _client) public view
        returns (bool _setApi, bool _setClient, uint _fpVersion, bytes28 _fpApi, bytes28 _fpClient, uint _tsApi, uint _tsClient, RequestType _rtApi, RequestType _rtClient, bool _matches) {

        Fingerprint memory fp = fingerprints[_dataId].clientFingerprints[_client].versions[_version];
        bool matches = fingerprintMatch(_dataId, _version, _client);

        return (fp.setApi,
            fp.setClient,
            fp.fpVersion,
            fp.fpApi,
            fp.fpClient,
            fp.apiTime,
            fp.clientTime,
            fp.apiRType,
            fp.clientRType,
            matches);
    }

    // HELPERS
    function addressInArray(address[] memory _addresses, address _addr) private view returns (bool) {
        for (uint i = 0; i < _addresses.length; ++i) {
            if (_addresses[i] == _addr) {
                return true;
            }
        }
        return false;
    }

    /**
     * Get an approximation of the current time
     * @return uint The unix timestamp (UTC)
     */
    function getCurrentTime() internal view returns (uint) {
        return block.timestamp;
    }

    /**
     * Check whether two strings are equal.
     * @return bool True iff both strings are equal
     */
    function stringCompare(string memory a, string memory b) public view returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))) );
    }

    /**
     * Check whether two strings are equal.
     * @return bool True iff both strings are equal
     */
    function fpCompare(bytes28 a, bytes28 b) public view returns (bool) {
        return a==b;
    }

    /**
     * Returns the maximum of two values
     */
    function max(uint a, uint b) internal pure returns (uint) {
        return a >= b ? a : b;
    }

    function fingerprintMatch(bytes12 _dataId, uint _version, address _client) internal view returns (bool) {
        if (fingerprints[_dataId].clientFingerprints[_client].versions[_version].setClient) {
            if (fingerprints[_dataId].clientFingerprints[_client].versions[_version].setApi) {
                bytes28 fpc = fingerprints[_dataId].clientFingerprints[_client].versions[_version].fpClient;
                bytes28 fpa = fingerprints[_dataId].clientFingerprints[_client].versions[_version].fpApi;
                if (fpCompare(fpc, fpa)) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * default function
     */
    function() payable external {}

}
