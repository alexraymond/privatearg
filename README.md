# privatearg

This is the repository for the code used in the paper Agree to Disagree: Subjective Fairness in Privacy-Restricted Decentralised Conflict Resolution.

If you would like to use this code, please cite
```buildoutcfg
@misc{raymond2021agree,
      title={Agree to Disagree: Subjective Fairness in Privacy-Restricted Decentralised Conflict Resolution}, 
      author={Alex Raymond and Matthew Malencia and Guilherme Paulino-Passos and Amanda Prorok},
      year={2021},
      eprint={2107.00032},
      archivePrefix={arXiv},
      primaryClass={cs.MA}
}
```

Note that this code is not final and further 'housekeeping' might take place. We apologise for any inconvenience.

This implementation is separated in two main parts. The files in the root folder contain the main
dialogue and privacy-aware argumentation mechanisms.

The `boat_sim` folder contains a graphical multi-agent simulation
where agents avoid collisions according to privacy-aware argumentation strategies, implemented using Arcade.
![Example screenshot](boat_sim/screenshot5.png)

Contact: Alex Raymond (alex.raymond@cl.cam.ac.uk)