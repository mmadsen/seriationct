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
    label "assemblage-5-2"
    xcoord 5
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
  edge [
    source 0
    target 1
    distance 3.60555127546
    name "assemblage-2-4*assemblage-5-2"
    weight 0.277350098113
    normalized_weight 0.218363874131
    unnormalized_weight 0.277350098113
    to_node "assemblage-5-2"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 2
    distance 1.0
    name "assemblage-2-4*assemblage-1-4"
    weight 1.0
    normalized_weight 0.0605632419144
    unnormalized_weight 1.0
    to_node "assemblage-1-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 3
    distance 2.82842712475
    name "assemblage-2-4*assemblage-4-2"
    weight 0.353553390593
    normalized_weight 0.171298716193
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-2"
    from_node "assemblage-2-4"
  ]
  edge [
    source 1
    target 2
    distance 4.472135955
    name "assemblage-1-4*assemblage-5-2"
    weight 0.22360679775
    normalized_weight 0.270847051717
    unnormalized_weight 0.22360679775
    to_node "assemblage-5-2"
    from_node "assemblage-1-4"
  ]
  edge [
    source 1
    target 3
    distance 1.0
    name "assemblage-4-2*assemblage-5-2"
    weight 1.0
    normalized_weight 0.0605632419144
    unnormalized_weight 1.0
    to_node "assemblage-5-2"
    from_node "assemblage-4-2"
  ]
  edge [
    source 2
    target 3
    distance 3.60555127546
    name "assemblage-4-2*assemblage-1-4"
    weight 0.277350098113
    normalized_weight 0.218363874131
    unnormalized_weight 0.277350098113
    to_node "assemblage-1-4"
    from_node "assemblage-4-2"
  ]
]
