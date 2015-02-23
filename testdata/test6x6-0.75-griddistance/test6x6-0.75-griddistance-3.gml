graph [
  is_directed 0
  node [
    id 0
    label "assemblage-4-1"
    xcoord 4
    ycoord 1
  ]
  node [
    id 1
    label "assemblage-3-2"
    xcoord 3
    ycoord 2
  ]
  node [
    id 2
    label "assemblage-2-3"
    xcoord 2
    ycoord 3
  ]
  node [
    id 3
    label "assemblage-4-2"
    xcoord 4
    ycoord 2
  ]
  node [
    id 4
    label "assemblage-5-4"
    xcoord 5
    ycoord 4
  ]
  edge [
    source 0
    target 1
    distance 1.41421356237
    name "assemblage-4-1*assemblage-3-2"
    weight 0.707106781187
    normalized_weight 0.0664512442366
    unnormalized_weight 0.707106781187
    to_node "assemblage-3-2"
    from_node "assemblage-4-1"
  ]
  edge [
    source 0
    target 2
    distance 2.82842712475
    name "assemblage-2-3*assemblage-4-1"
    weight 0.353553390593
    normalized_weight 0.132902488473
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-1"
    from_node "assemblage-2-3"
  ]
  edge [
    source 0
    target 3
    distance 1.0
    name "assemblage-4-2*assemblage-4-1"
    weight 1.0
    normalized_weight 0.046988125418
    unnormalized_weight 1.0
    to_node "assemblage-4-1"
    from_node "assemblage-4-2"
  ]
  edge [
    source 0
    target 4
    distance 3.16227766017
    name "assemblage-5-4*assemblage-4-1"
    weight 0.316227766017
    normalized_weight 0.148589499302
    unnormalized_weight 0.316227766017
    to_node "assemblage-4-1"
    from_node "assemblage-5-4"
  ]
  edge [
    source 1
    target 2
    distance 1.41421356237
    name "assemblage-2-3*assemblage-3-2"
    weight 0.707106781187
    normalized_weight 0.0664512442366
    unnormalized_weight 0.707106781187
    to_node "assemblage-3-2"
    from_node "assemblage-2-3"
  ]
  edge [
    source 1
    target 3
    distance 1.0
    name "assemblage-4-2*assemblage-3-2"
    weight 1.0
    normalized_weight 0.046988125418
    unnormalized_weight 1.0
    to_node "assemblage-3-2"
    from_node "assemblage-4-2"
  ]
  edge [
    source 1
    target 4
    distance 2.82842712475
    name "assemblage-5-4*assemblage-3-2"
    weight 0.353553390593
    normalized_weight 0.132902488473
    unnormalized_weight 0.353553390593
    to_node "assemblage-3-2"
    from_node "assemblage-5-4"
  ]
  edge [
    source 2
    target 3
    distance 2.2360679775
    name "assemblage-2-3*assemblage-4-2"
    weight 0.4472135955
    normalized_weight 0.10506864257
    unnormalized_weight 0.4472135955
    to_node "assemblage-4-2"
    from_node "assemblage-2-3"
  ]
  edge [
    source 2
    target 4
    distance 3.16227766017
    name "assemblage-5-4*assemblage-2-3"
    weight 0.316227766017
    normalized_weight 0.148589499302
    unnormalized_weight 0.316227766017
    to_node "assemblage-2-3"
    from_node "assemblage-5-4"
  ]
  edge [
    source 3
    target 4
    distance 2.2360679775
    name "assemblage-5-4*assemblage-4-2"
    weight 0.4472135955
    normalized_weight 0.10506864257
    unnormalized_weight 0.4472135955
    to_node "assemblage-4-2"
    from_node "assemblage-5-4"
  ]
]
