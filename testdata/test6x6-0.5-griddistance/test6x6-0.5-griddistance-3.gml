graph [
  is_directed 0
  node [
    id 0
    label "assemblage-4-4"
    xcoord 4
    ycoord 4
  ]
  node [
    id 1
    label "assemblage-4-5"
    xcoord 4
    ycoord 5
  ]
  node [
    id 2
    label "assemblage-4-3"
    xcoord 4
    ycoord 3
  ]
  node [
    id 3
    label "assemblage-1-1"
    xcoord 1
    ycoord 1
  ]
  node [
    id 4
    label "assemblage-2-3"
    xcoord 2
    ycoord 3
  ]
  edge [
    source 0
    target 1
    distance 1.0
    name "assemblage-4-4*assemblage-4-5"
    weight 1.0
    normalized_weight 0.0382427384547
    unnormalized_weight 1.0
    to_node "assemblage-4-5"
    from_node "assemblage-4-4"
  ]
  edge [
    source 0
    target 2
    distance 1.0
    name "assemblage-4-4*assemblage-4-3"
    weight 1.0
    normalized_weight 0.0382427384547
    unnormalized_weight 1.0
    to_node "assemblage-4-3"
    from_node "assemblage-4-4"
  ]
  edge [
    source 0
    target 3
    distance 4.24264068712
    name "assemblage-4-4*assemblage-1-1"
    weight 0.235702260396
    normalized_weight 0.162250198155
    unnormalized_weight 0.235702260396
    to_node "assemblage-1-1"
    from_node "assemblage-4-4"
  ]
  edge [
    source 0
    target 4
    distance 2.2360679775
    name "assemblage-4-4*assemblage-2-3"
    weight 0.4472135955
    normalized_weight 0.0855133628305
    unnormalized_weight 0.4472135955
    to_node "assemblage-2-3"
    from_node "assemblage-4-4"
  ]
  edge [
    source 1
    target 2
    distance 2.0
    name "assemblage-4-5*assemblage-4-3"
    weight 0.5
    normalized_weight 0.0764854769094
    unnormalized_weight 0.5
    to_node "assemblage-4-3"
    from_node "assemblage-4-5"
  ]
  edge [
    source 1
    target 3
    distance 5.0
    name "assemblage-4-5*assemblage-1-1"
    weight 0.2
    normalized_weight 0.191213692274
    unnormalized_weight 0.2
    to_node "assemblage-1-1"
    from_node "assemblage-4-5"
  ]
  edge [
    source 1
    target 4
    distance 2.82842712475
    name "assemblage-4-5*assemblage-2-3"
    weight 0.353553390593
    normalized_weight 0.10816679877
    unnormalized_weight 0.353553390593
    to_node "assemblage-2-3"
    from_node "assemblage-4-5"
  ]
  edge [
    source 2
    target 3
    distance 3.60555127546
    name "assemblage-4-3*assemblage-1-1"
    weight 0.277350098113
    normalized_weight 0.137886154413
    unnormalized_weight 0.277350098113
    to_node "assemblage-1-1"
    from_node "assemblage-4-3"
  ]
  edge [
    source 2
    target 4
    distance 2.0
    name "assemblage-4-3*assemblage-2-3"
    weight 0.5
    normalized_weight 0.0764854769094
    unnormalized_weight 0.5
    to_node "assemblage-2-3"
    from_node "assemblage-4-3"
  ]
  edge [
    source 3
    target 4
    distance 2.2360679775
    name "assemblage-2-3*assemblage-1-1"
    weight 0.4472135955
    normalized_weight 0.0855133628305
    unnormalized_weight 0.4472135955
    to_node "assemblage-1-1"
    from_node "assemblage-2-3"
  ]
]
