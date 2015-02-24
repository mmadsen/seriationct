graph [
  is_directed 0
  node [
    id 0
    label "assemblage-1-4"
    xcoord 1
    ycoord 4
  ]
  node [
    id 1
    label "assemblage-3-2"
    xcoord 3
    ycoord 2
  ]
  node [
    id 2
    label "assemblage-2-1"
    xcoord 2
    ycoord 1
  ]
  node [
    id 3
    label "assemblage-1-1"
    xcoord 1
    ycoord 1
  ]
  node [
    id 4
    label "assemblage-4-3"
    xcoord 4
    ycoord 3
  ]
  edge [
    source 0
    target 1
    distance 2.82842712475
    name "assemblage-1-4*assemblage-3-2"
    weight 0.353553390593
    normalized_weight 0.114736717002
    unnormalized_weight 0.353553390593
    to_node "assemblage-3-2"
    from_node "assemblage-1-4"
  ]
  edge [
    source 0
    target 2
    distance 3.16227766017
    name "assemblage-1-4*assemblage-2-1"
    weight 0.316227766017
    normalized_weight 0.128279549366
    unnormalized_weight 0.316227766017
    to_node "assemblage-2-1"
    from_node "assemblage-1-4"
  ]
  edge [
    source 0
    target 3
    distance 3.0
    name "assemblage-1-4*assemblage-1-1"
    weight 0.333333333333
    normalized_weight 0.121696665965
    unnormalized_weight 0.333333333333
    to_node "assemblage-1-1"
    from_node "assemblage-1-4"
  ]
  edge [
    source 0
    target 4
    distance 3.16227766017
    name "assemblage-1-4*assemblage-4-3"
    weight 0.316227766017
    normalized_weight 0.128279549366
    unnormalized_weight 0.316227766017
    to_node "assemblage-4-3"
    from_node "assemblage-1-4"
  ]
  edge [
    source 1
    target 2
    distance 1.41421356237
    name "assemblage-2-1*assemblage-3-2"
    weight 0.707106781187
    normalized_weight 0.0573683585011
    unnormalized_weight 0.707106781187
    to_node "assemblage-3-2"
    from_node "assemblage-2-1"
  ]
  edge [
    source 1
    target 3
    distance 2.2360679775
    name "assemblage-3-2*assemblage-1-1"
    weight 0.4472135955
    normalized_weight 0.0907073392443
    unnormalized_weight 0.4472135955
    to_node "assemblage-1-1"
    from_node "assemblage-3-2"
  ]
  edge [
    source 1
    target 4
    distance 1.41421356237
    name "assemblage-3-2*assemblage-4-3"
    weight 0.707106781187
    normalized_weight 0.0573683585011
    unnormalized_weight 0.707106781187
    to_node "assemblage-4-3"
    from_node "assemblage-3-2"
  ]
  edge [
    source 2
    target 4
    distance 2.82842712475
    name "assemblage-2-1*assemblage-4-3"
    weight 0.353553390593
    normalized_weight 0.114736717002
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-3"
    from_node "assemblage-2-1"
  ]
  edge [
    source 2
    target 3
    distance 1.0
    name "assemblage-2-1*assemblage-1-1"
    weight 1.0
    normalized_weight 0.0405655553217
    unnormalized_weight 1.0
    to_node "assemblage-1-1"
    from_node "assemblage-2-1"
  ]
  edge [
    source 3
    target 4
    distance 3.60555127546
    name "assemblage-1-1*assemblage-4-3"
    weight 0.277350098113
    normalized_weight 0.14626118973
    unnormalized_weight 0.277350098113
    to_node "assemblage-4-3"
    from_node "assemblage-1-1"
  ]
]
