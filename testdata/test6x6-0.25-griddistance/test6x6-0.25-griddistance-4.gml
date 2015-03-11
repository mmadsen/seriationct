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
    label "assemblage-5-5"
    xcoord 5
    ycoord 5
  ]
  edge [
    source 0
    target 1
    distance 1.0
    name "assemblage-2-4*assemblage-3-4"
    weight 1.0
    normalized_weight 0.156290400149
    unnormalized_weight 1.0
    to_node "assemblage-3-4"
    from_node "assemblage-2-4"
  ]
  edge [
    source 0
    target 2
    distance 3.16227766017
    name "assemblage-5-5*assemblage-2-4"
    weight 0.316227766017
    normalized_weight 0.494233640889
    unnormalized_weight 0.316227766017
    to_node "assemblage-2-4"
    from_node "assemblage-5-5"
  ]
  edge [
    source 1
    target 2
    distance 2.2360679775
    name "assemblage-5-5*assemblage-3-4"
    weight 0.4472135955
    normalized_weight 0.349475958963
    unnormalized_weight 0.4472135955
    to_node "assemblage-3-4"
    from_node "assemblage-5-5"
  ]
]
