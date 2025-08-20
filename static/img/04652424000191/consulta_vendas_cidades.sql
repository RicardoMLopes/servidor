SELECT cidade,sum(valortotal) from movnota
WHERE datalancamento >= '2013-05-20 00:00'
and datalancamento <= '2013-05-25 23:59'
GROUP BY cidade
order by valortotal DESC