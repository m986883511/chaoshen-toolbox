$n = Get-NetIPConfiguration | select InterfaceIndex, IPv4Address, InterfaceAlias, InterfaceDescription, NetAdapter
ForEach( $a in $n ){
    $a.Ipv4Address =  $a.Ipv4Address.IpAddress
    $a | Add-Member -type NoteProperty -name Status -value $a.NetAdapter.Status
    $a.PSObject.Properties.Remove('NetAdapter')
}

# $n
$n | ConvertTo-Json