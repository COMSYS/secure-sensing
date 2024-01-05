# Securing Sensing in Supply Chains: Opportunities, Building Blocks, and Designs

## About
This repository contains/points to our evaluation artifacts that enable end-to-end-secured sensing in complex IoT-based supply chains.

> Supply chains increasingly develop toward complex networks, both technically in terms of devices and connectivity, and also anthropogenic with a growing number of actors. The lack of mutual trust in such networks results in challenges that are exacerbated by stringent requirements for shipping conditions or quality, and where actors may attempt to reduce costs or cover up incidents. In this paper, we develop and comprehensively study four scenarios that eventually lead to end-to-end-secured sensing in complex IoT-based supply chains with many mutually distrusting actors, while highlighting relevant pitfalls and challenges–-details that are still missing in related work. Our designs ensure that sensed data is securely transmitted and stored, and can be verified by all parties. To prove practical feasibility, we evaluate the most elaborate design with regard to performance, cost, deployment, and also trust implications on the basis of prevalent (mis)use cases. Our work enables a notion of secure end-to-end sensing with minimal trust across the system stack, even for complex and opaque supply chain networks.

## Publication

- Jan Pennekamp, Fritz Alder, Lennart Bader, Gianluca Scopelliti, Klaus Wehrle, and Jan Tobias Mühlberg: *Securing Sensing in Supply Chains: Opportunities, Building Blocks, and Designs*. IEEE Access, IEEE, 2024.

If you use any portion of our work, please cite our publication.

```bibtex
@inproceedings{pennekamp2024securing,
    author = {Pennekamp, Jan and Alder, Fritz and Bader, Lennart and Scopelliti, Gianluca and Wehrle, Klaus and M{\"u}hlberg, Jan Tobias},
    title = {{Securing Sensing in Supply Chains: Opportunities, Building Blocks, and Designs}},
    journal = {IEEE Access},
    year = {2024},
    publisher = {IEEE},
    doi = {10.1109/ACCESS.2024.3350778},
    issn = {2169-3536},
}
```

## License

We refer to the source code contained in *this* repository as "program" hereafter.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.

If you are planning to integrate parts of our work into a commercial product and do not want to disclose your source code, please contact us for other licensing options via email at pennekamp (at) comsys (dot) rwth-aachen (dot) de

## Acknowledgments

Funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy – EXC-2023 Internet of Production – 390621612.
This research is funded by the Research Fund KU Leuven.
This research has received funding under EU H2020 MSCA-ITN action 5GhOSTS, grant agreement no. 814035.
[Fritz Alder](https://falder.org/) is supported by a grant of the Research Foundation -- Flanders (FWO).
Eduard Vlad supported the artifact creation of our blockchain performance evaluation.

---

## Evaluation Artifacts

In accordance with our evaluations conducted and presented in our paper, we provide the architectures' codes for additional technical insights and reproducibility.
Following the structure of Section V.A, we provide the following artifacts:

1. The code, results and evaluation scripts for the **Sensing and Processing Equipment**, covered in Section V.A.1), are in the dedicated [AuthenticExecution repository](https://github.com/AuthenticExecution/examples/blob/main/supply-chain/) that contains multiple examples beyond the application within supply chain settings.
2. The code and evaluation scripts for the multi-hop supply chain transparency framework are in the subfolder `ledger-evaluation`, which is part of Section V.A.3).
    * This framework includes the implementation for the interaction with the **Distributed Ledger**, which is based on [Quorum](https://consensys.net/quorum/).
    * Note that the evaluation requires existing data for deriving fingerprints and preparing the blockchain transactions.
    * The code is partly taken from our full-fledged supply chain information system [PrivAccIChain](https://github.com/COMSYS/PrivAccIChain).