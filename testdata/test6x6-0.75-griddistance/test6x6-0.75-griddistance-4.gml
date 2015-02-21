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
    label "assemblage-3-4"
    xcoord 3
    ycoord 4
  ]
  node [
    id 2
    label "assemblage-4-4"
    xcoord 4
    ycoord 4
  ]
  node [
    id 3
    label "assemblage-2-1"
    xcoord 2
    ycoord 1
  ]
  node [
    id 4
    label "assemblage-4-1"
    xcoord 4
    ycoord 1
  ]
  edge [
    source 0
    target 1
    distance 1.0
    name "assemblage-2-4*assemblage-3-4"
    weight 0.0391609256766
    normalized_weight 0.0391609256766
    unnormalized_weight 1.0
    to_node "assemblage-3-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 2
    distance 2.0
    name "assemblage-2-4*assemblage-4-4"
    weight 0.0783218513532
    normalized_weight 0.0783218513532
    unnormalized_weight 0.5
    to_node "assemblage-4-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 3
    distance 3.0
    name "assemblage-2-4*assemblage-2-1"
    weight 0.11748277703
    normalized_weight 0.11748277703
    unnormalized_weight 0.333333333333
    to_node "assemblage-2-1"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 4
    distance 3.60555127546
    name "assemblage-2-4*assemblage-4-1"
    weight 0.141196725522
    normalized_weight 0.141196725522
    unnormalized_weight 0.277350098113
    to_node "assemblage-4-1"
    from_node "assemblage-2-4"
  ]
  edge [
    source 1
    target 2
    distance 1.0
    name "assemblage-4-4*assemblage-3-4"
    weight 0.0391609256766
    normalized_weight 0.0391609256766
    unnormalized_weight 1.0
    to_node "assemblage-3-4"
    from_node "assemblage-4-4"
  ]
  edge [
    source 1
    target 3
    distance 3.16227766017
    name "assemblage-2-1*assemblage-3-4"
    weight 0.123837720419
    normalized_weight 0.123837720419
    unnormalized_weight 0.316227766017
    to_node "assemblage-3-4"
    from_node "assemblage-2-1"
  ]
  edge [
    source 1
    target 4
    distance 3.16227766017
    name "assemblage-4-1*assemblage-3-4"
    weight 0.123837720419
    normalized_weight 0.123837720419
    unnormalized_weight 0.316227766017
    to_node "assemblage-3-4"
    from_node "assemblage-4-1"
  ]
  edge [
    source 2
    target 3
    distance 3.60555127546
    name "assemblage-4-4*assemblage-2-1"
    weight 0.141196725522
    normalized_weight 0.141196725522
    unnormalized_weight 0.277350098113
    to_node "assemblage-2-1"
    from_node "assemblage-4-4"
  ]
  edge [
    source 2
    target 4
    distance 3.0
    name "assemblage-4-4*assemblage-4-1"
    weight 0.11748277703
    normalized_weight 0.11748277703
    unnormalized_weight 0.333333333333
    to_node "assemblage-4-1"
    from_node "assemblage-4-4"
  ]
  edge [
    source 3
    target 4
    distance 2.0
    name "assemblage-2-1*assemblage-4-1"
    weight 0.0783218513532
    normalized_weight 0.0783218513532
    unnormalized_weight 0.5
    to_node "assemblage-4-1"
    from_node "assemblage-2-1"
  ]
]
