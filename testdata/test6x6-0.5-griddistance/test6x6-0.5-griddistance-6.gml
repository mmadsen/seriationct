graph [
  is_directed 0
  node [
    id 0
    label "assemblage-2-4"
    xcoord 2
    ycoord 4
  ]
  node [
    id 1
    label "assemblage-5-3"
    xcoord 5
    ycoord 3
  ]
  node [
    id 2
    label "assemblage-3-1"
    xcoord 3
    ycoord 1
  ]
  node [
    id 3
    label "assemblage-3-4"
    xcoord 3
    ycoord 4
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
    distance 3.16227766017
    name "assemblage-2-4*assemblage-5-3"
    weight 0.316227766017
    normalized_weight 0.126518425793
    unnormalized_weight 0.316227766017
    to_node "assemblage-5-3"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 2
    distance 3.16227766017
    name "assemblage-2-4*assemblage-3-1"
    weight 0.316227766017
    normalized_weight 0.126518425793
    unnormalized_weight 0.316227766017
    to_node "assemblage-3-1"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 3
    distance 1.0
    name "assemblage-2-4*assemblage-3-4"
    weight 1.0
    normalized_weight 0.0400086391486
    unnormalized_weight 1.0
    to_node "assemblage-3-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 4
    distance 3.0
    name "assemblage-2-4*assemblage-5-4"
    weight 0.333333333333
    normalized_weight 0.120025917446
    unnormalized_weight 0.333333333333
    to_node "assemblage-5-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 1
    target 2
    distance 2.82842712475
    name "assemblage-5-3*assemblage-3-1"
    weight 0.353553390593
    normalized_weight 0.113161520192
    unnormalized_weight 0.353553390593
    to_node "assemblage-3-1"
    from_node "assemblage-5-3"
  ]
  edge [
    source 1
    target 3
    distance 2.2360679775
    name "assemblage-5-3*assemblage-3-4"
    weight 0.4472135955
    normalized_weight 0.0894620368235
    unnormalized_weight 0.4472135955
    to_node "assemblage-3-4"
    from_node "assemblage-5-3"
  ]
  edge [
    source 1
    target 4
    distance 1.0
    name "assemblage-5-3*assemblage-5-4"
    weight 1.0
    normalized_weight 0.0400086391486
    unnormalized_weight 1.0
    to_node "assemblage-5-4"
    from_node "assemblage-5-3"
  ]
  edge [
    source 2
    target 3
    distance 3.0
    name "assemblage-3-1*assemblage-3-4"
    weight 0.333333333333
    normalized_weight 0.120025917446
    unnormalized_weight 0.333333333333
    to_node "assemblage-3-4"
    from_node "assemblage-3-1"
  ]
  edge [
    source 2
    target 4
    distance 3.60555127546
    name "assemblage-3-1*assemblage-5-4"
    weight 0.277350098113
    normalized_weight 0.144253199912
    unnormalized_weight 0.277350098113
    to_node "assemblage-5-4"
    from_node "assemblage-3-1"
  ]
  edge [
    source 3
    target 4
    distance 2.0
    name "assemblage-3-4*assemblage-5-4"
    weight 0.5
    normalized_weight 0.0800172782972
    unnormalized_weight 0.5
    to_node "assemblage-5-4"
    from_node "assemblage-3-4"
  ]
]
