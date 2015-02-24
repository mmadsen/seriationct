graph [
  is_directed 0
  node [
    id 0
    label "assemblage-4-5"
    xcoord 4
    ycoord 5
  ]
  node [
    id 1
    label "assemblage-4-1"
    xcoord 4
    ycoord 1
  ]
  node [
    id 2
    label "assemblage-2-3"
    xcoord 2
    ycoord 3
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
    distance 4.0
    name "assemblage-4-5*assemblage-4-1"
    weight 0.25
    normalized_weight 0.157565127696
    unnormalized_weight 0.25
    to_node "assemblage-4-1"
    from_node "assemblage-4-5"
  ]
  edge [
    source 0
    target 2
    distance 2.82842712475
    name "assemblage-2-3*assemblage-4-5"
    weight 0.353553390593
    normalized_weight 0.111415370273
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-5"
    from_node "assemblage-2-3"
  ]
  edge [
    source 0
    target 3
    distance 1.41421356237
    name "assemblage-4-5*assemblage-3-4"
    weight 0.707106781187
    normalized_weight 0.0557076851363
    unnormalized_weight 0.707106781187
    to_node "assemblage-3-4"
    from_node "assemblage-4-5"
  ]
  edge [
    source 0
    target 4
    distance 1.41421356237
    name "assemblage-5-4*assemblage-4-5"
    weight 0.707106781187
    normalized_weight 0.0557076851363
    unnormalized_weight 0.707106781187
    to_node "assemblage-4-5"
    from_node "assemblage-5-4"
  ]
  edge [
    source 1
    target 2
    distance 2.82842712475
    name "assemblage-2-3*assemblage-4-1"
    weight 0.353553390593
    normalized_weight 0.111415370273
    unnormalized_weight 0.353553390593
    to_node "assemblage-4-1"
    from_node "assemblage-2-3"
  ]
  edge [
    source 1
    target 3
    distance 3.16227766017
    name "assemblage-4-1*assemblage-3-4"
    weight 0.316227766017
    normalized_weight 0.124566170834
    unnormalized_weight 0.316227766017
    to_node "assemblage-3-4"
    from_node "assemblage-4-1"
  ]
  edge [
    source 1
    target 4
    distance 3.16227766017
    name "assemblage-5-4*assemblage-4-1"
    weight 0.316227766017
    normalized_weight 0.124566170834
    unnormalized_weight 0.316227766017
    to_node "assemblage-4-1"
    from_node "assemblage-5-4"
  ]
  edge [
    source 2
    target 3
    distance 1.41421356237
    name "assemblage-2-3*assemblage-3-4"
    weight 0.707106781187
    normalized_weight 0.0557076851363
    unnormalized_weight 0.707106781187
    to_node "assemblage-3-4"
    from_node "assemblage-2-3"
  ]
  edge [
    source 2
    target 4
    distance 3.16227766017
    name "assemblage-5-4*assemblage-2-3"
    weight 0.316227766017
    normalized_weight 0.124566170834
    unnormalized_weight 0.316227766017
    to_node "assemblage-2-3"
    from_node "assemblage-5-4"
  ]
  edge [
    source 3
    target 4
    distance 2.0
    name "assemblage-5-4*assemblage-3-4"
    weight 0.5
    normalized_weight 0.0787825638481
    unnormalized_weight 0.5
    to_node "assemblage-3-4"
    from_node "assemblage-5-4"
  ]
]
