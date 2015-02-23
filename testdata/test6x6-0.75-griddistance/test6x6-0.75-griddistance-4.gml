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
    label "assemblage-3-2"
    xcoord 3
    ycoord 2
  ]
  node [
    id 2
    label "assemblage-1-4"
    xcoord 1
    ycoord 4
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
    distance 2.2360679775
    name "assemblage-2-4*assemblage-3-2"
    weight 0.4472135955
    normalized_weight 0.0874729383773
    unnormalized_weight 0.4472135955
    to_node "assemblage-3-2"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 2
    distance 1.0
    name "assemblage-1-4*assemblage-2-4"
    weight 1.0
    normalized_weight 0.0391190872807
    unnormalized_weight 1.0
    to_node "assemblage-2-4"
    from_node "assemblage-1-4"
  ]
  edge [
    source 0
    target 3
    distance 2.82842712475
    name "assemblage-2-4*assemblage-4-2"
    weight 0.353553390593
    normalized_weight 0.11064548756
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-2"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 4
    distance 3.0
    name "assemblage-5-4*assemblage-2-4"
    weight 0.333333333333
    normalized_weight 0.117357261842
    unnormalized_weight 0.333333333333
    to_node "assemblage-2-4"
    from_node "assemblage-5-4"
  ]
  edge [
    source 1
    target 2
    distance 2.82842712475
    name "assemblage-1-4*assemblage-3-2"
    weight 0.353553390593
    normalized_weight 0.11064548756
    unnormalized_weight 0.353553390593
    to_node "assemblage-3-2"
    from_node "assemblage-1-4"
  ]
  edge [
    source 1
    target 3
    distance 1.0
    name "assemblage-4-2*assemblage-3-2"
    weight 1.0
    normalized_weight 0.0391190872807
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
    normalized_weight 0.11064548756
    unnormalized_weight 0.353553390593
    to_node "assemblage-3-2"
    from_node "assemblage-5-4"
  ]
  edge [
    source 2
    target 3
    distance 3.60555127546
    name "assemblage-1-4*assemblage-4-2"
    weight 0.277350098113
    normalized_weight 0.14104587504
    unnormalized_weight 0.277350098113
    to_node "assemblage-4-2"
    from_node "assemblage-1-4"
  ]
  edge [
    source 2
    target 4
    distance 4.0
    name "assemblage-1-4*assemblage-5-4"
    weight 0.25
    normalized_weight 0.156476349123
    unnormalized_weight 0.25
    to_node "assemblage-5-4"
    from_node "assemblage-1-4"
  ]
  edge [
    source 3
    target 4
    distance 2.2360679775
    name "assemblage-5-4*assemblage-4-2"
    weight 0.4472135955
    normalized_weight 0.0874729383773
    unnormalized_weight 0.4472135955
    to_node "assemblage-4-2"
    from_node "assemblage-5-4"
  ]
]
